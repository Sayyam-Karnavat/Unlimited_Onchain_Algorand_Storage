# 🧩 Blockchain Image Uploader

## 📄 Overview
**Blockchain Image Uploader** is a proof-of-concept decentralized storage system built on top of blockchain technology.  
This demo showcases a **pure blockchain-backed storage system**, where the **entire image file** is stored, retrieved, and displayed directly from the blockchain — without relying on off-chain systems like IPFS or centralized databases.

Due to the free-tier cloud deployment used for this demonstration:
- Only **image files (PNG, JPG, JPEG)** are accepted  
- Maximum **file size is limited to 100 KB**  

This ensures the demo remains lightweight while still proving that true on-chain storage and retrieval are functioning end-to-end.

---

## ⚙️ Setup & Installation

Follow these steps to run the project locally:

### 1. Clone the repository
```bash
git clonehttps://github.com/Sayyam-Karnavat/Unlimited_Onchain_Algorand_Storage.git
cd Unlimited_Onchain_Algorand_Storage
```


### 2.Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```


### 4. Run the Streamlit application

```bash
streamlit run app.py
```


### Smart Contract / Blockchain Asset Links

<p> Link <p>


### 🧠 Architecture Overview

- While complete implementation details are intentionally abstracted, the system’s design utilizes:

- Global and Box Storage Combination: A hybrid use of on-chain storage primitives for efficiency and scalability.

- Custom Encoding Logic: Files are encoded and split intelligently to fit blockchain transaction constraints.

- Retrieval Pipeline: Reassembles and decodes file data directly from blockchain state.

- Streamlit Frontend: Provides a user-friendly interface to upload, store, and retrieve files in real time.


### Deployed Frontend :- The project’s frontend demo is deployed here:

- 🔗 https://private-unlimited-onchain-algorand.onrender.com
