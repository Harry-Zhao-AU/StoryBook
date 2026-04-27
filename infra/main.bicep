@description('Short name used in resource names — lowercase letters and numbers only, max 10 chars')
param appName string = 'storybook'

@description('Azure region for all resources. Must support Azure Static Web Apps.')
param location string = 'australiaeast'

@description('SWA hostname (e.g. blue-ocean-123.azurestaticapps.net). Leave empty on first deploy; fill in and redeploy to set CORS.')
param swaHostname string = ''

var storageAccountName = '${take(appName, 10)}${uniqueString(resourceGroup().id)}'

var corsOrigins = empty(swaHostname)
  ? ['http://localhost:4280']
  : ['https://${swaHostname}', 'http://localhost:4280']

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: true
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: corsOrigins
          allowedMethods: ['GET']
          allowedHeaders: ['*']
          exposedHeaders: []
          maxAgeInSeconds: 3600
        }
      ]
    }
  }
}

resource storiesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'stories'
  properties: { publicAccess: 'Blob' }
}

resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: '${appName}-swa'
  location: location
  sku: { name: 'Free', tier: 'Free' }
  properties: {}
}

output storageAccountName string = storageAccount.name
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output swaDefaultHostname string = staticWebApp.properties.defaultHostname
