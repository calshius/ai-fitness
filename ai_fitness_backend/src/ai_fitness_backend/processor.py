import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from .database import Document, Embedding

class FitnessDataProcessor:
    def __init__(self, data_dir="data", db: Session = None):
        self.data_dir = data_dir
        self.nutrition_data = None
        self.exercise_data = None
        self.measurement_data = None
        self.garmin_activities = None
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.document_embeddings = None
        self.documents = None
        self.db = db
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.join(self.data_dir, "mfp"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "garmin"), exist_ok=True)

    def load_data(self):
        """Load all CSV data files"""
        # Load nutrition data
        nutrition_files = [f for f in os.listdir(os.path.join(self.data_dir, "mfp")) 
                          if f.startswith("Nutrition-Summary")]
        if nutrition_files:
            nutrition_path = os.path.join(self.data_dir, "mfp", nutrition_files[0])
            self.nutrition_data = pd.read_csv(nutrition_path)
            self.nutrition_data["Date"] = pd.to_datetime(self.nutrition_data["Date"])

        # Load exercise data
        exercise_files = [f for f in os.listdir(os.path.join(self.data_dir, "mfp")) 
                         if f.startswith("Exercise-Summary")]
        if exercise_files:
            exercise_path = os.path.join(self.data_dir, "mfp", exercise_files[0])
            self.exercise_data = pd.read_csv(exercise_path)
            self.exercise_data["Date"] = pd.to_datetime(self.exercise_data["Date"])

        # Load measurement data
        measurement_files = [f for f in os.listdir(os.path.join(self.data_dir, "mfp")) 
                            if f.startswith("Measurement-Summary")]
        if measurement_files:
            measurement_path = os.path.join(self.data_dir, "mfp", measurement_files[0])
            self.measurement_data = pd.read_csv(measurement_path)
            self.measurement_data["Date"] = pd.to_datetime(self.measurement_data["Date"])

        # Load Garmin activities
        garmin_files = [f for f in os.listdir(os.path.join(self.data_dir, "garmin")) 
                       if f.startswith("Activities")]
        if garmin_files:
            garmin_path = os.path.join(self.data_dir, "garmin", garmin_files[0])
            self.garmin_activities = pd.read_csv(garmin_path)
            self.garmin_activities["Date"] = pd.to_datetime(self.garmin_activities["Date"])

        print("All data loaded successfully!")

    def create_documents(self):
        """Create text documents from the data for embedding"""
        documents = []

        # Create nutrition documents
        if self.nutrition_data is not None:
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

        # Create exercise documents
        if self.exercise_data is not None:
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

        # Create measurement documents
        if self.measurement_data is not None:
            for _, row in self.measurement_data.iterrows():
                date_str = row["Date"].strftime("%Y-%m-%d")
                doc = f"Date: {date_str}. Measurement: Weight {row['Weight']} kg."
                documents.append({"text": doc, "type": "measurement", "date": date_str})

        # Create Garmin activity documents
        if self.garmin_activities is not None:
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

        # Add summary documents
        if self.nutrition_data is not None:
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
            initial_weight = self.measurement_data.iloc[0]["Weight"]
            final_weight = self.measurement_data.iloc[-1]["Weight"]
            weight_change = final_weight - initial_weight

            weight_doc = (
                f"Weight trend: Started at {initial_weight} kg and ended at {final_weight} kg. "
                f"Total change: {weight_change:.1f} kg over the period."
            )
            documents.append({"text": weight_doc, "type": "summary", "date": "all"})

        self.documents = documents
        print(f"Created {len(documents)} documents from the data")
        
        # Store documents in database if db session is available
        if self.db:
            self.store_documents_in_db()
            
        return documents
    
    def store_documents_in_db(self):
        """Store documents in the database"""
        if not self.documents:
            return
        
        # Clear existing documents and embeddings
        self.db.query(Embedding).delete()
        self.db.query(Document).delete()
        self.db.commit()
        
        # Add new documents
        db_documents = []
        for doc in self.documents:
            db_doc = Document(
                text=doc["text"],
                type=doc["type"],
                date=doc["date"]
            )
            self.db.add(db_doc)
            db_documents.append(db_doc)
        
        self.db.commit()
        
        # Create embeddings for documents
        texts = [doc["text"] for doc in self.documents]
        embeddings = self.model.encode(texts)
        
        # Store embeddings
        for i, (doc, embedding) in enumerate(zip(db_documents, embeddings)):
            db_embedding = Embedding(
                document_id=doc.id,
                embedding=embedding.tobytes()  # Convert numpy array to bytes for storage
            )
            self.db.add(db_embedding)
            
        self.db.commit()
        print(f"Stored {len(db_documents)} documents and embeddings in the database")

    def load_documents_from_db(self):
        """Load documents from the database"""
        if not self.db:
            return
        
        db_documents = self.db.query(Document).all()
        self.documents = [
            {"text": doc.text, "type": doc.type, "date": doc.date}
            for doc in db_documents
        ]
        print(f"Loaded {len(self.documents)} documents from the database")
        
        # Load embeddings
        db_embeddings = self.db.query(Embedding).all()
        if db_embeddings:
            # Convert bytes back to numpy arrays
            self.document_embeddings = np.array([
                np.frombuffer(emb.embedding, dtype=np.float32)
                for emb in db_embeddings
            ])
            print(f"Loaded {len(self.document_embeddings)} embeddings from the database")
        
        return self.documents

    def create_embeddings(self):
        """Create embeddings for all documents"""
        if self.documents is None:
            if self.db:
                self.load_documents_from_db()
            else:
                self.create_documents()
                
        if self.document_embeddings is not None:
            return self.document_embeddings

        texts = [doc["text"] for doc in self.documents]
        self.document_embeddings = self.model.encode(texts)
        print("Created embeddings for all documents")
        return self.document_embeddings

    def retrieve_relevant_documents(self, query, top_k=5):
        """Retrieve the most relevant documents for a query"""
        if self.document_embeddings is None:
            self.create_embeddings()

        # Encode the query
        query_embedding = self.model.encode([query])[0]

        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.document_embeddings)[0]

        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Return top k documents and their similarity scores
        results = []
        for idx in top_indices:
            results.append(
                {"document": self.documents[idx], "similarity": similarities[idx]}
            )

        return results

    def generate_context_from_query(self, query, top_k=5):
        """Generate a context string from relevant documents for a query"""
        relevant_docs = self.retrieve_relevant_documents(query, top_k)

        context = f"Based on the following fitness and nutrition data:\n\n"
        for i, doc in enumerate(relevant_docs):
            context += f"{i+1}. {doc['document']['text']}\n"

        return context
