---
outline: deep
---

<script setup lang="ts">
    import apiData from './api_data.ts';
    import { fmtCurlCmd, fmtPodyCmd, fmtPodxCmd } from './api_data.ts';
    import APIBlock from './api_block.vue';
    import APITable from './api_table.vue';
    import { ref, watch } from 'vue';

    const urlParams = new URLSearchParams(window.location.search);
    const initialApiType = urlParams.get('api') || 'podx' as 'curl' | 'podx' | 'pody';
    const apiType = ref( initialApiType as 'curl' | 'podx' | 'pody');
    watch(apiType, (newType) => {
        urlParams.set('api', newType);
        window.history.replaceState({}, '', `${window.location.pathname}?${urlParams.toString()}`);
    });
</script>

# HTTP API

The API exposes interface for managing your own pods and query server status.  
- `GET` method is used for querying data without side effects;  
- `POST` method is used for creating or updating data.
- All parameters are passed via query string in URLs.
- The response is always in json format.

## Summary
<APITable :api-data="apiData" />

## Details
<div style="margin-block: 0.5rem; padding: 0.5rem; background-color: var(--vp-c-gray-soft); border-radius: 0.5rem;">
    <label class="api-type-span">
        <input type="radio" v-model="apiType" value="podx" class="mr-2">
        <span>podx</span>
    </label>
    <label class="api-type-span">
        <input type="radio" v-model="apiType" value="pody" class="mr-2">
        <span>pody</span>
    </label>
    <label class="api-type-span">
        <input type="radio" v-model="apiType" value="curl" class="mr-2">
        <span>curl</span>
    </label>
</div>
<template v-if="apiType === 'curl'">

::: tip
Here examples of API calls are provided using `curl` utility.  
It is supposed that the pody server is running on `10.254.29.178:8799`. 
Please replace it with your own server address.  
For better readability, you can format the output using `python -m json.tool`:  
```sh
curl -s ... | python -m json.tool
```
:::
</template>
<template v-else-if="apiType === 'podx'">

::: tip
Here examples of API calls are provided using `podx` utility.  
`podx` is a shorthand for `pody fetch` command, please refer to [here](./pody-cli#podx) for more information.
:::
</template>
<template v-else>

::: tip
Here examples of API calls are provided using `pody` utility.   
More information about the client-side CLI utilities can be found at [here](./pody-cli).
:::
</template>

<template v-for="apiName in Object.keys(apiData)">

<APIBlock :api-name="apiName" :api-desc="apiData[apiName]">
<template v-if="apiData[apiName].example && apiType === 'curl'">

```sh-vue
{{`${fmtCurlCmd( apiData[apiName].method, apiName, apiData[apiName].example.input)} `}}
```
</template>

<template v-else-if="apiData[apiName].example && apiType === 'pody'">

```sh-vue
{{`${fmtPodyCmd( apiData[apiName].method, apiName, apiData[apiName].example.input)} `}}
```
</template>

<template v-else-if="apiData[apiName].example && apiType === 'podx'">

```sh-vue
{{`${fmtPodxCmd( apiData[apiName].method, apiName, apiData[apiName].example.input)} `}}
```
</template>

</APIBlock>

</template>

<style scoped>
.api-type-span {
    display: inline-block;
    margin-right: 0.5rem;
}
input[type="radio"] {
    margin-right: 0.25rem;
}
</style>