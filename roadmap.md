# ReviewGuard – Project Roadmap

## Project Overview
ReviewGuard is an Online Review Fraud Detection System that combines DBMS concepts with Machine Learning to detect suspicious or fake reviews on online platforms. The system stores review data in a relational database, extracts behavioral features using SQL, and applies a Random Forest model to identify potentially fraudulent reviews.

---

# Phase 1: Problem Definition

## Goals
- Detect suspicious or fake reviews
- Analyze user behavioral patterns
- Generate fraud probability scores
- Provide administrative reports

## Key Outcomes
- Clear problem statement
- Defined system scope
- Dataset requirements identified

---

# Phase 2: System Design

## Architecture
System consists of three layers:

1. Database Layer
2. Machine Learning Layer
3. Reporting Layer

### High Level Flow
User Review → Database → Feature Extraction → ML Model → Fraud Score → Admin Reports

---

# Phase 3: Database Design

## Entities
- Users
- Products
- Reviews
- Review_Features
- Review_Log
- ML_Fraud_Result
- Fraud_Flag

## Tasks
- Create ER Diagram (Chen Model)
- Define relationships
- Normalize tables
- Create relational schema

## Deliverables
- ER Diagram
- SQL Schema

---

# Phase 4: Database Implementation

## Steps
1. Create database
2. Implement tables
3. Add primary and foreign keys
4. Add constraints
5. Implement triggers for logging

## Sample Data
Insert realistic sample data for:
- Normal users
- Suspicious users
- Various products and reviews

---

# Phase 5: Feature Engineering

Extract behavioral features from database using SQL.

## Features
- Reviews in last 1 hour
- Reviews in last 24 hours
- Average rating by user
- Rating deviation from product average
- Review length
- Account age
- Similarity score

## Output
Store extracted features in `Review_Features` table.

---

# Phase 6: Machine Learning Model

## Model Selection
Random Forest Classifier

## Tasks
- Export feature dataset
- Split dataset into training and testing
- Train ML model
- Evaluate model performance

## Evaluation Metrics
- Accuracy
- Precision
- Recall
- F1 Score

---

# Phase 7: Fraud Prediction

## Steps
1. Run trained model on review features
2. Generate fraud probability score
3. Classify reviews as suspicious or genuine

## Storage
Save results into `ML_Fraud_Result` table.

---

# Phase 8: Fraud Flagging

## Rules
Flag reviews when:
- Fraud score exceeds threshold
- Abnormal review frequency detected

## Storage
Store flagged reviews in `Fraud_Flag` table.

---

# Phase 9: Reporting and Analysis

## Reports
- Suspicious users
- Highly flagged products
- High-risk reviews

## Implementation
Create SQL views for reporting.

---

# Phase 10: Testing

## Test Cases
- Normal review behavior
- High-frequency review spam
- Extreme rating patterns

## Validation
Verify:
- Correct fraud detection
- Database integrity
- Query performance

---

# Phase 11: Documentation

## Required Documents
- Abstract
- Problem Statement
- ER Diagram
- Database Schema
- System Architecture
- ML Methodology
- Results

---

# Phase 12: Final Deliverables

- Working database
- Trained ML model
- Fraud detection results
- Project report
- Presentation slides

---

# Suggested Project Timeline

Week 1-2: Problem definition and research

Week 3: ER diagram and schema design

Week 4: Database implementation

Week 5: Feature extraction

Week 6: Machine learning model

Week 7: Fraud prediction and reporting

Week 8: Testing and documentation

---

# Future Improvements

- NLP analysis of review text
- Real-time fraud detection
- Web dashboard for administrators
- Advanced anomaly detection models

