# PowerShell deployment script for Windows
# Azure Container App Deployment Script for Zone Plate Generator

param(
    [string]$ResourceGroup = "zone-plate-generator-rg",
    [string]$Location = "eastus",
    [string]$EnvironmentName = "zone-plate-env",
    [string]$AppName = "zone-plate-generator",
    [string]$RegistryName = "zoneplateregistry",
    [string]$ImageName = "zone-plate-generator",
    [string]$Tag = "latest"
)

Write-Host "🚀 Starting Azure Container App deployment..." -ForegroundColor Green

# Check if Azure CLI is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Login check
try {
    az account show | Out-Null
} catch {
    Write-Host "🔑 Please log in to Azure..." -ForegroundColor Yellow
    az login
}

# Create resource group
Write-Host "📦 Creating resource group..." -ForegroundColor Blue
az group create --name $ResourceGroup --location $Location

# Create container registry
Write-Host "🏗️  Creating container registry..." -ForegroundColor Blue
az acr create --resource-group $ResourceGroup --name $RegistryName --sku Basic --admin-enabled true

# Build and push image
Write-Host "🔨 Building and pushing Docker image..." -ForegroundColor Blue
az acr build --registry $RegistryName --image "${ImageName}:${Tag}" .

# Create Container Apps environment
Write-Host "🌍 Creating Container Apps environment..." -ForegroundColor Blue
az containerapp env create --name $EnvironmentName --resource-group $ResourceGroup --location $Location

# Get registry credentials
Write-Host "🔐 Getting registry credentials..." -ForegroundColor Blue
$RegistryLoginServer = az acr show --name $RegistryName --resource-group $ResourceGroup --query loginServer --output tsv
$RegistryUsername = az acr credential show --name $RegistryName --resource-group $ResourceGroup --query username --output tsv
$RegistryPassword = az acr credential show --name $RegistryName --resource-group $ResourceGroup --query passwords[0].value --output tsv

# Generate secret key
$SecretKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString() + (New-Guid).ToString()))

# Create container app
Write-Host "🚢 Creating container app..." -ForegroundColor Blue
az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $EnvironmentName `
    --image "$RegistryLoginServer/${ImageName}:${Tag}" `
    --registry-login-server $RegistryLoginServer `
    --registry-username $RegistryUsername `
    --registry-password $RegistryPassword `
    --target-port 8000 `
    --ingress 'external' `
    --min-replicas 1 `
    --max-replicas 10 `
    --cpu 0.5 `
    --memory 1Gi `
    --env-vars "FLASK_ENV=production" "PORT=8000" "DEBUG=false" "SECRET_KEY=$SecretKey"

# Get the application URL
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
$AppUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv
Write-Host "📍 Your Zone Plate Generator is available at: https://$AppUrl" -ForegroundColor Cyan

Write-Host "💡 To update the app in the future, run:" -ForegroundColor Yellow
Write-Host "   az acr build --registry $RegistryName --image ${ImageName}:${Tag} ." -ForegroundColor Gray
Write-Host "   az containerapp update --name $AppName --resource-group $ResourceGroup --image $RegistryLoginServer/${ImageName}:${Tag}" -ForegroundColor Gray
