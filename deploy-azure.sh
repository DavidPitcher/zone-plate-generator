#!/bin/bash

# Azure Container App Deployment Script for Zone Plate Generator

set -e

# Configuration
RESOURCE_GROUP="zone-plate-generator-rg"
LOCATION="eastus"
ENVIRONMENT_NAME="zone-plate-env"
APP_NAME="zone-plate-generator"
REGISTRY_NAME="zoneplateregistry"
IMAGE_NAME="zone-plate-generator"
TAG="latest"

echo "🚀 Starting Azure Container App deployment..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login check
if ! az account show &> /dev/null; then
    echo "🔑 Please log in to Azure..."
    az login
fi

# Create resource group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Create container registry
echo "🏗️  Creating container registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true

# Build and push image
echo "🔨 Building and pushing Docker image..."
az acr build \
    --registry $REGISTRY_NAME \
    --image $IMAGE_NAME:$TAG \
    .

# Create Container Apps environment
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Get registry credentials
echo "🔐 Getting registry credentials..."
REGISTRY_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Generate secret key
SECRET_KEY=$(openssl rand -base64 32)

# Create container app
echo "🚢 Creating container app..."
az containerapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $REGISTRY_LOGIN_SERVER/$IMAGE_NAME:$TAG \
    --registry-login-server $REGISTRY_LOGIN_SERVER \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --target-port 8000 \
    --ingress 'external' \
    --min-replicas 1 \
    --max-replicas 10 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        "FLASK_ENV=production" \
        "PORT=8000" \
        "DEBUG=false" \
        "SECRET_KEY=$SECRET_KEY"

# Get the application URL
echo "🎉 Deployment completed!"
APP_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)
echo "📍 Your Zone Plate Generator is available at: https://$APP_URL"

echo "💡 To update the app in the future, run:"
echo "   az acr build --registry $REGISTRY_NAME --image $IMAGE_NAME:$TAG ."
echo "   az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP --image $REGISTRY_LOGIN_SERVER/$IMAGE_NAME:$TAG"
