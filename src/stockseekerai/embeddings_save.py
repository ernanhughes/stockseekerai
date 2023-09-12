import os
import pickle
import sys
import time

import chromadb
from dotenv import load_dotenv
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import StorageContext, ServiceContext, LangchainEmbedding
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores import ChromaVectorStore

CHUNK_SIZE = 512
CHUNK_OVERLAP = 32
TRAIN_CUTOFF_YEAR = 2017
NUM_SAMPLES_TRAIN = 1000
NUM_SAMPLES_TEST = 500


def save_index(embeddings_path, embedding_model, symbol, ar_date, config_dict):
    db = chromadb.PersistentClient(path=os.path.join(embeddings_path, symbol, ar_date))
    chroma_collection = db.create_collection("ar_date")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    service_context = ServiceContext.from_defaults(embed_model=embedding_model,
                                                   chunk_size=CHUNK_SIZE,
                                                   chunk_overlap=CHUNK_OVERLAP)
    ar_filing_path = os.path.join(os.getenv('annual_reports_pdf_save_directory'), symbol, ar_date)
    documents = SimpleDirectoryReader(ar_filing_path).load_data()
    _ = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, service_context=service_context
    )


def save_embeddings(df, embedding_model, save_directory, config_dict):
    for i in df.index:
        start_time = time.time()
        curr_series = df.loc[i]
        symbol = curr_series['symbol']
        ar_date = curr_series['report_date'].date().strftime('%Y-%m-%d')
        save_path = os.path.join(save_directory, symbol, ar_date)
        if os.path.exists(save_path):
            continue
        save_index(save_directory, embedding_model,
                   symbol, ar_date, config_dict)
        print("Completed: {}, {}, {} in {:.2f}s".format(i + 1, symbol, ar_date, time.time() - start_time))


def save_dfs(df_train, df_test):
    with open(os.getenv('targets_train_df_path'), 'wb') as handle:
        pickle.dump(df_train, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.getenv('targets_test_df_path'), 'wb') as handle:
        pickle.dump(df_test, handle, protocol=pickle.HIGHEST_PROTOCOL)


def embeddings():
    load_dotenv()
    # Read the targets df generated from make_targets.py
    with open(os.getenv('targets_df_path'), 'rb') as handle:
        df_targets = pickle.load(handle)
    df_targets_train = df_targets.loc[lambda x: x.era <= TRAIN_CUTOFF_YEAR].reset_index(drop=True)
    df_targets_test = df_targets.loc[lambda x: x.era > TRAIN_CUTOFF_YEAR].reset_index(drop=True)
    df_targets_train_sampled = df_targets_train.sample(n=NUM_SAMPLES_TRAIN).reset_index(drop=True)
    df_targets_test_sampled = df_targets_test.sample(n=NUM_SAMPLES_TEST).reset_index(drop=True)
    save_dfs(df_targets_train_sampled, df_targets_test_sampled)
    embedding_model = LangchainEmbedding(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    )
    save_embeddings(df_targets_train_sampled, embedding_model,
                    os.getenv('embeddings_for_training_directory'))
    save_embeddings(df_targets_test_sampled, embedding_model,
                    os.getenv('embeddings_for_testing_directory'))


if __name__ == '__main__':
    embeddings()
    sys.exit(0)
