import os
import time
import logging
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from .database import Document, Embedding

# Set up logging
logger = logging.getLogger("ai_fitness_api.processor")


class FitnessDataProcessor:
    def __init__(self, data_dir="data", db: Session = None):
        logger.info(f"Initializing FitnessDataProcessor with data_dir={data_dir}")
        self.data_dir = data_dir
        self.nutrition_data = None
        self.exercise_data = None
        self.measurement_data = None
        self.garmin_activities = None
        logger.info("Loading SentenceTransformer model")
        start_time = time.time()
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info(
                f"SentenceTransformer model loaded in {time.time() - start_time:.2f} seconds"
            )
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model: {str(e)}")
            raise

        self.document_embeddings = None
        self.documents = None
        self.db = db

        # Create data directory if it doesn't exist
        try:
            os.makedirs(os.path.join(self.data_dir, "mfp"), exist_ok=True)
            os.makedirs(os.path.join(self.data_dir, "garmin"), exist_ok=True)
            logger.info("Data directories created/verified")
        except Exception as e:
            logger.error(f"Error creating data directories: {str(e)}")
            raise

    def load_data(self):
        """Load all CSV data files"""
        logger.info("Loading data files")

        # Load nutrition data
        try:
            nutrition_files = [
                f
                for f in os.listdir(os.path.join(self.data_dir, "mfp"))
                if f.startswith("Nutrition-Summary")
            ]
            if nutrition_files:
                nutrition_path = os.path.join(self.data_dir, "mfp", nutrition_files[0])
                logger.info(f"Loading nutrition data from {nutrition_path}")
                self.nutrition_data = pd.read_csv(nutrition_path)
                self.nutrition_data["Date"] = pd.to_datetime(
                    self.nutrition_data["Date"]
                )
                logger.info(f"Loaded {len(self.nutrition_data)} nutrition records")
            else:
                logger.warning("No nutrition files found")
        except Exception as e:
            logger.error(f"Error loading nutrition data: {str(e)}")

        # Load exercise data
        try:
            exercise_files = [
                f
                for f in os.listdir(os.path.join(self.data_dir, "mfp"))
                if f.startswith("Exercise-Summary")
            ]
            if exercise_files:
                exercise_path = os.path.join(self.data_dir, "mfp", exercise_files[0])
                logger.info(f"Loading exercise data from {exercise_path}")
                self.exercise_data = pd.read_csv(exercise_path)
                self.exercise_data["Date"] = pd.to_datetime(self.exercise_data["Date"])
                logger.info(f"Loaded {len(self.exercise_data)} exercise records")
            else:
                logger.warning("No exercise files found")
        except Exception as e:
            logger.error(f"Error loading exercise data: {str(e)}")
        # Load measurement data
        try:
            measurement_files = [
                f
                for f in os.listdir(os.path.join(self.data_dir, "mfp"))
                if f.startswith("Measurement-Summary")
            ]
            if measurement_files:
                measurement_path = os.path.join(
                    self.data_dir, "mfp", measurement_files[0]
                )
                logger.info(f"Loading measurement data from {measurement_path}")
                self.measurement_data = pd.read_csv(measurement_path)
                self.measurement_data["Date"] = pd.to_datetime(
                    self.measurement_data["Date"]
                )
                logger.info(f"Loaded {len(self.measurement_data)} measurement records")
            else:
                logger.warning("No measurement files found")
        except Exception as e:
            logger.error(f"Error loading measurement data: {str(e)}")

        # Load Garmin activities
        try:
            garmin_files = [
                f
                for f in os.listdir(os.path.join(self.data_dir, "garmin"))
                if f.startswith("Activities")
            ]
            if garmin_files:
                garmin_path = os.path.join(self.data_dir, "garmin", garmin_files[0])
                logger.info(f"Loading Garmin activities from {garmin_path}")
                self.garmin_activities = pd.read_csv(garmin_path)
                self.garmin_activities["Date"] = pd.to_datetime(
                    self.garmin_activities["Date"]
                )
                logger.info(f"Loaded {len(self.garmin_activities)} Garmin activities")
            else:
                logger.warning("No Garmin files found")
        except Exception as e:
            logger.error(f"Error loading Garmin data: {str(e)}")

        logger.info("Data loading completed")

    def create_documents(self):
        """Create text documents from the data for embedding"""
        logger.info("Creating documents from loaded data")
        start_time = time.time()
        documents = []

        # Create nutrition documents
        if self.nutrition_data is not None:
            logger.info("Processing nutrition data into documents")
            nutrition_docs_count = 0
            for date, group in self.nutrition_data.groupby("Date"):
                date_str = date.strftime("%Y-%m-%d")
                daily_calories = group["Calories"].sum()
                daily_protein = group["Protein (g)"].sum()
                daily_carbs = group["Carbohydrates (g)"].sum()
                daily_fat = group["Fat (g)"].sum()

                doc = (
                    f"Date: {date_str}. Nutrition summary: Total calories: {daily_calories:.1f}, "
                    f"Protein: {daily_protein:.1f}g, Carbs: {daily_carbs:.1f}g, Fat: {daily_fat:.1f}g. "
                )

                # Add meal details
                for _, row in group.iterrows():
                    doc += (
                        f"{row['Meal']}: Calories {row['Calories']:.1f}, Protein {row['Protein (g)']:.1f}g, "
                        f"Carbs {row['Carbohydrates (g)']:.1f}g, Fat {row['Fat (g)']:.1f}g. "
                    )

                documents.append({"text": doc, "type": "nutrition", "date": date_str})
                nutrition_docs_count += 1
            logger.info(f"Created {nutrition_docs_count} nutrition documents")

        # Create exercise documents
        if self.exercise_data is not None:
            logger.info("Processing exercise data into documents")
            exercise_docs_count = 0
            for date, group in self.exercise_data.groupby("Date"):
                date_str = date.strftime("%Y-%m-%d")
                total_calories = group["Exercise Calories"].sum()
                total_minutes = group["Exercise Minutes"].sum()
                steps = group["Steps"].sum()

                doc = (
                    f"Date: {date_str}. Exercise summary: Burned {total_calories:.1f} calories, "
                    f"Exercised for {total_minutes} minutes, Steps: {steps}. "
                )

                # Add exercise details
                for _, row in group.iterrows():
                    if pd.notna(row["Exercise"]):
                        doc += (
                            f"Activity: {row['Exercise']}, Duration: {row['Exercise Minutes']} minutes, "
                            f"Calories: {row['Exercise Calories']}. "
                        )

                documents.append({"text": doc, "type": "exercise", "date": date_str})
                exercise_docs_count += 1
            logger.info(f"Created {exercise_docs_count} exercise documents")

        # Create measurement documents
        if self.measurement_data is not None:
            logger.info("Processing measurement data into documents")
            measurement_docs_count = 0
            for _, row in self.measurement_data.iterrows():
                date_str = row["Date"].strftime("%Y-%m-%d")
                doc = f"Date: {date_str}. Measurement: Weight {row['Weight']} kg."
                documents.append({"text": doc, "type": "measurement", "date": date_str})
                measurement_docs_count += 1
            logger.info(f"Created {measurement_docs_count} measurement documents")

        # Create Garmin activity documents
        if self.garmin_activities is not None:
            logger.info("Processing Garmin activities into documents")
            garmin_docs_count = 0
            for _, row in self.garmin_activities.iterrows():
                date_str = row["Date"].strftime("%Y-%m-%d %H:%M:%S")
                doc = (
                    f"Date: {date_str}. Garmin activity: {row['Activity Type']}, "
                    f"Duration: {row['Total Time']}, Calories: {row['Calories']}"
                )

                if pd.notna(row["Distance"]) and float(row["Distance"]) > 0:
                    doc += f", Distance: {row['Distance']} km"

                if pd.notna(row["Avg HR"]):
                    doc += f", Average HR: {row['Avg HR']}"

                if pd.notna(row["Max HR"]):
                    doc += f", Max HR: {row['Max HR']}"

                documents.append({"text": doc, "type": "garmin", "date": date_str})
                garmin_docs_count += 1
            logger.info(f"Created {garmin_docs_count} Garmin activity documents")

        # Add summary documents
        if self.nutrition_data is not None:
            logger.info("Creating nutrition summary document")
            avg_daily_calories = (
                self.nutrition_data.groupby("Date")["Calories"].sum().mean()
            )
            avg_daily_protein = (
                self.nutrition_data.groupby("Date")["Protein (g)"].sum().mean()
            )
            avg_daily_carbs = (
                self.nutrition_data.groupby("Date")["Carbohydrates (g)"].sum().mean()
            )
            avg_daily_fat = self.nutrition_data.groupby("Date")["Fat (g)"].sum().mean()

            summary_doc = (
                f"Nutrition summary for the entire period: Average daily calories: {avg_daily_calories:.1f}, "
                f"Average daily protein: {avg_daily_protein:.1f}g, Average daily carbs: {avg_daily_carbs:.1f}g, "
                f"Average daily fat: {avg_daily_fat:.1f}g."
            )
            documents.append({"text": summary_doc, "type": "summary", "date": "all"})

        # Weight trend
        if self.measurement_data is not None and not self.measurement_data.empty:
            logger.info("Creating weight trend summary document")
            initial_weight = self.measurement_data.iloc[0]["Weight"]
            final_weight = self.measurement_data.iloc[-1]["Weight"]
            weight_change = final_weight - initial_weight

            weight_doc = (
                f"Weight trend: Started at {initial_weight} kg and ended at {final_weight} kg. "
                f"Total change: {weight_change:.1f} kg over the period."
            )
            documents.append({"text": weight_doc, "type": "summary", "date": "all"})

        self.documents = documents
        logger.info(
            f"Created {len(documents)} documents from the data in {time.time() - start_time:.2f} seconds"
        )

        # Store documents in database if db session is available
        if self.db:
            self.store_documents_in_db()

        return documents

    def store_documents_in_db(self):
        """Store documents in the database"""
        if not self.documents:
            logger.warning("No documents to store in database")
            return

        logger.info(f"Storing {len(self.documents)} documents in database")
        start_time = time.time()

        try:
            # Clear existing documents and embeddings
            logger.info("Clearing existing documents and embeddings")
            self.db.query(Embedding).delete()
            self.db.query(Document).delete()
            self.db.commit()

            # Add new documents
            logger.info("Adding new documents to database")
            db_documents = []
            for doc in self.documents:
                db_doc = Document(text=doc["text"], type=doc["type"], date=doc["date"])
                self.db.add(db_doc)
                db_documents.append(db_doc)

            self.db.commit()
            logger.info(f"Added {len(db_documents)} documents to database")

            # Create embeddings for documents
            logger.info("Creating embeddings for documents")
            texts = [doc["text"] for doc in self.documents]
            embeddings = self.model.encode(texts)

            # Store embeddings
            logger.info("Storing embeddings in database")
            for i, (doc, embedding) in enumerate(zip(db_documents, embeddings)):
                db_embedding = Embedding(
                    document_id=doc.id,
                    embedding=embedding.tobytes(),  # Convert numpy array to bytes for storage
                )
                self.db.add(db_embedding)

            self.db.commit()
            logger.info(
                f"Stored {len(db_documents)} documents and embeddings in the database in {time.time() - start_time:.2f} seconds"
            )
        except Exception as e:
            logger.error(f"Error storing documents in database: {str(e)}")
            self.db.rollback()
            raise

    def load_documents_from_db(self):
        """Load documents from the database"""
        if not self.db:
            logger.warning("No database session available to load documents")
            return

        logger.info("Loading documents from database")
        start_time = time.time()

        try:
            db_documents = self.db.query(Document).all()
            self.documents = [
                {"text": doc.text, "type": doc.type, "date": doc.date}
                for doc in db_documents
            ]
            logger.info(f"Loaded {len(self.documents)} documents from the database")

            # Load embeddings
            logger.info("Loading embeddings from database")
            db_embeddings = self.db.query(Embedding).all()
            if db_embeddings:
                # Convert bytes back to numpy arrays
                self.document_embeddings = np.array(
                    [
                        np.frombuffer(emb.embedding, dtype=np.float32)
                        for emb in db_embeddings
                    ]
                )
                logger.info(
                    f"Loaded {len(self.document_embeddings)} embeddings from the database in {time.time() - start_time:.2f} seconds"
                )
            else:
                logger.warning("No embeddings found in database")
        except Exception as e:
            logger.error(f"Error loading documents from database: {str(e)}")
            raise

        return self.documents

    def create_embeddings(self):
        """Create embeddings for all documents"""
        if self.documents is None:
            logger.info(
                "No documents found, attempting to load from database or create new ones"
            )
            if self.db:
                self.load_documents_from_db()
            else:
                self.create_documents()

        if self.document_embeddings is not None:
            logger.info("Embeddings already exist, returning existing embeddings")
            return self.document_embeddings

        logger.info(f"Creating embeddings for {len(self.documents)} documents")
        start_time = time.time()
        texts = [doc["text"] for doc in self.documents]
        try:
            self.document_embeddings = self.model.encode(texts)
            logger.info(
                f"Created embeddings for all documents in {time.time() - start_time:.2f} seconds"
            )
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise

        return self.document_embeddings

    def retrieve_relevant_documents(self, query, top_k=5):
        """Retrieve the most relevant documents for a query"""
        logger.info(f"Retrieving top {top_k} documents for query: {query}")
        start_time = time.time()

        if self.document_embeddings is None:
            logger.info("No embeddings found, creating embeddings")
            self.create_embeddings()

        # Encode the query
        logger.info("Encoding query")
        try:
            query_embedding = self.model.encode([query])[0]

            # Calculate similarities
            logger.info("Calculating similarities")
            similarities = cosine_similarity(
                [query_embedding], self.document_embeddings
            )[0]

            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Return top k documents and their similarity scores
            results = []
            for idx in top_indices:
                results.append(
                    {"document": self.documents[idx], "similarity": similarities[idx]}
                )

            logger.info(
                f"Retrieved {len(results)} relevant documents in {time.time() - start_time:.2f} seconds"
            )
            for i, result in enumerate(results):
                logger.info(
                    f"Document {i+1}: similarity={result['similarity']:.4f}, type={result['document']['type']}, date={result['document']['date']}"
                )

            return results
        except Exception as e:
            logger.error(f"Error retrieving relevant documents: {str(e)}")
            raise

    def generate_context_from_query(self, query, top_k=5):
        """Generate a context string from relevant documents for a query"""
        logger.info(f"Generating context for query: {query} with top_k={top_k}")
        start_time = time.time()

        relevant_docs = self.retrieve_relevant_documents(query, top_k)

        context = f"Based on the following fitness and nutrition data:\n\n"
        for i, doc in enumerate(relevant_docs):
            context += f"{i+1}. {doc['document']['text']}\n"

        logger.info(
            f"Generated context with {len(relevant_docs)} documents in {time.time() - start_time:.2f} seconds"
        )
        logger.info(f"Context length: {len(context)} characters")
        return context
