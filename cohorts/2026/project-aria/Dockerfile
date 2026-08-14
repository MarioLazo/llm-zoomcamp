FROM python:3.11-slim
WORKDIR /project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# `streamlit run <script>` only adds the script's own directory to sys.path,
# not the cwd — without this, `from app import monitoring` in both
# app/streamlit_app.py and monitoring/dashboard.py fails with
# "ModuleNotFoundError: No module named 'app'" (found by actually loading
# the UI in a browser; every prior test used `python -c`/`python -m`, which
# don't hit this path).
ENV PYTHONPATH=/project
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0"]
