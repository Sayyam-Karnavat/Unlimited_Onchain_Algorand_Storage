import algokit_utils
from algosdk.util import microalgos_to_algos
import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from algosdk import transaction as wc_transaction
from Blockchain.artifact import (
    HelloWorldFactory,
    SetStorageArgs
)
import os
from dotenv import load_dotenv

load_dotenv()


assert os.environ['MNEMONIC'] is not None


class MnemeBlockchain:
    def __init__(self, network="localnet"):
        self.network = network
        if network.lower() == "localnet":
            self.algorand = algokit_utils.AlgorandClient.default_localnet()
            self.deployer_ = self.algorand.account.localnet_dispenser()
        elif network.lower() == "testnet":
            self.algorand = algokit_utils.AlgorandClient.testnet()
            self.deployer_ = self.algorand.account.from_mnemonic(mnemonic=os.environ['MNEMONIC'])
        elif network.lower() == "mainnet":
            print("Mainnet under development \n Choose either 'localnet' or 'testnet' ")
            return None
        else:
            print("Invalid network \n Choose either 'localnet' or 'testnet' ")

        self.indexer_client = self.algorand.client.indexer
        self.transaction_file = "all_transactions.json"
        self.output_filename = "retrieved_file"
        self.__deploy()

    def __deploy(self):
        print("Starting App deployment ...\n")
        self.factory = self.algorand.client.get_typed_app_factory(
            HelloWorldFactory, default_sender=self.deployer_.address
        )
        self.app_client, self.result = self.factory.deploy(
            on_update=algokit_utils.OnUpdate.AppendApp,
            on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        )
        if self.result.operation_performed in [
            algokit_utils.OperationPerformed.Create,
            algokit_utils.OperationPerformed.Replace,
        ]:
            self.algorand.send.payment(
                algokit_utils.PaymentParams(
                    amount=algokit_utils.AlgoAmount(algo=10),
                    sender=self.deployer_.address,
                    receiver=self.app_client.app_address,
                )
            )
        print(f"Application successfully deployed on {self.network}")
        print(f"App ID :- {self.app_client.app_id}")
        print(f"App Address :- {self.app_client.app_address}")

    def upload(self, filename: str):
        self.file_extension = str(filename).split(".")[-1]
        with open(filename, "rb") as f:
            serialized_data = f.read()

        CHUNK_SIZE = int(0.9 * 1024)
        serialized_chunks = [serialized_data[i: i+CHUNK_SIZE] for i in range(0, len(serialized_data), CHUNK_SIZE)]
        all_transactions = {}

        def upload_chunk(idx, chunk):
            suggested_params = self.algorand.get_suggested_params()
            self.algorand.set_suggested_params_cache(suggested_params=suggested_params)
            response = self.app_client.send.set_storage(
                args=SetStorageArgs(
                    key=1,
                    val=chunk,
                )
            )
            transaction_ID = response.tx_id
            wc_transaction.wait_for_confirmation(txid=transaction_ID, algod_client=self.algorand.client.algod)
            return idx, transaction_ID

        self.algorand.set_suggested_params_cache_timeout(0)
        self.algorand.set_default_validity_window(1000)

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_chunk = {executor.submit(upload_chunk, idx, chunk): idx for idx, chunk in enumerate(serialized_chunks)}
            for i, future in enumerate(as_completed(future_to_chunk)):
                if i % 10 == 0:
                    print(f"Chunks processed: {i}")
                idx, transaction_ID = future.result()
                all_transactions[idx] = transaction_ID

        all_transactions = dict(sorted(all_transactions.items(), key=lambda item: int(item[0])))
        with open(self.transaction_file, "w") as f:
            json.dump(fp=f, obj=all_transactions)

        print("\nCorrectly serialized and uploaded file on blockchain ...\n")
        print("Check all transactions in file: ", self.transaction_file)

    total_retry = 10


    @retry(
        stop=stop_after_attempt(total_retry),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: print(f"Retrying transaction {retry_state.attempt_number}...")
    )

    def fetch_transaction(self, transaction):
        response = self.indexer_client.search_transactions(txid=transaction)
        if 'transactions' not in response or not response['transactions']:
            raise ValueError(f"No transaction found for txid: {transaction}")
        return response

    def retrieve(self):
        with open(self.transaction_file, "r") as f:
            all_transactions = json.load(fp=f)
            all_transactions = dict(sorted(all_transactions.items(), key=lambda item: int(item[0])))

        retrieved_chunks = [None] * len(all_transactions)
        chunk_lengths = {}

        def process_transaction(idx_str, transaction):
            idx = int(idx_str)  # Convert string index to integer
            try:
                response = self.fetch_transaction(transaction)
                app_txn = response['transactions'][0]['application-transaction']
                app_args = app_txn['application-args']
                if len(app_args) < 3:
                    raise ValueError(f"Unexpected number of app args in tx {transaction}")
                val_b64 = app_args[-1]
                encoded_val = base64.b64decode(val_b64)
                if len(encoded_val) < 2:
                    raise ValueError(f"Invalid encoded val length in tx {transaction}")
                len_val = int.from_bytes(encoded_val[0:2], 'big')
                chunk = encoded_val[2:2 + len_val]
                if len(chunk) != len_val:
                    raise ValueError(f"Length mismatch in tx {transaction}: expected {len_val}, got {len(chunk)}")
                return idx, chunk, len_val
            except Exception as e:
                print(f"Error processing transaction {transaction}: {str(e)}")
                raise

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_tx = {executor.submit(process_transaction, idx, tx): idx for idx, tx in all_transactions.items()}
            for future in as_completed(future_to_tx):
                idx = future_to_tx[future]
                try:
                    idx, chunk, len_val = future.result()
                    retrieved_chunks[idx] = chunk
                    chunk_lengths[idx] = len_val
                    # print(f"Retrieved chunk {idx}")
                except Exception as e:
                    print(f"Failed to retrieve chunk {idx} after retries: {str(e)}")
                    return

        if None in retrieved_chunks:
            print("Some chunks failed to retrieve, cannot combine file.")
            return

        print("Gathered all chunks ... combining ...")
        combined_data = b''.join(retrieved_chunks)
        output_path = f"{self.output_filename}.{self.file_extension}"
        with open(output_path, "wb") as f:
            f.write(combined_data)

        print(f"Successfully combined and wrote data to {output_path}")

    def get_balance(self, address):
        balance_info = self.algorand.client.algod.account_info(address=address)
        balance = microalgos_to_algos(balance_info["amount"])
        print(f"\n Balance details {address} \n  :- {balance} Algos ")

if __name__ == "__main__":
    obj = MnemeBlockchain(network="localnet")
    obj.upload(filename="embedded_qr.png")
    obj.retrieve()