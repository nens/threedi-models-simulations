# 3Di Models &amp; Simulations QGIS plugin

## Model generation

Run the following docker command in the `threedi_models_simulations` folder:

`docker run --rm   -v ${PWD}:/local openapitools/openapi-generator-cli:v7.15.0 generate   -i /local/models/swagger.5d512c024c8f.json   -g python   -o /local --global-property models,modelTests=false,modelDocs=false --additional-properties=packageName=.`

Note that `swagger.5d512c024c8f.json` is the swagger openapi specification. Due to the `--global-property models` flag, the generator will only generate the model, not the API.
