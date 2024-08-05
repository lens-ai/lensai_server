from fastapi import FastAPI
from strawberry.asgi import GraphQL

app = FastAPI()

graphql_app = GraphQL(schema)
app.add_route("/graphql", graphql_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
