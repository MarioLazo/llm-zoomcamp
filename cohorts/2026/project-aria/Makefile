.PHONY: up down model ingest app dashboard logs

up:            ## start all services
	docker compose up -d --build

down:          ## stop all services
	docker compose down

model:         ## download the ONNX embedding model locally
	python ingestion/download_model.py

ingest:        ## run ingestion into Qdrant
	python -m ingestion.ingest

app:           ## run the Streamlit app locally
	streamlit run app/streamlit_app.py

dashboard:     ## run the monitoring dashboard locally
	streamlit run monitoring/dashboard.py --server.port 8502

logs:          ## tail compose logs
	docker compose logs -f
