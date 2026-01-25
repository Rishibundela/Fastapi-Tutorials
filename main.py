from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def hello():
  return {"message": "Hello World"}

@app.get('/about')
def about():
  return {"message": "Fastapi is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints."}