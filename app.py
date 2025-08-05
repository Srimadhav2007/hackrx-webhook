from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from llm_code import ragging, query_rag  # Assuming these functions are in llm_code2.py

app = FastAPI()

@app.post("/hackrx/run")
async def doc_load(request: Request):
    payload = await request.json()
    url = payload.get('documents')
    queries = payload.get('questions')

    if not url or not queries:
        return JSONResponse(content={"error": "Missing 'documents' or 'questions' in payload"}, status_code=400)

    try:
        retriever = ragging(url)
        answers = []
        for q in queries:
            answers.append(query_rag(query_text=q, retriever=retriever))
        return JSONResponse({"answers": answers})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
