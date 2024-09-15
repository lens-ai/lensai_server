from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from schema import schema

app = FastAPI()

graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

