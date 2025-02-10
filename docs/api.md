---
outline: deep
---

<script setup lang="ts">
    import apiData from './api_data.ts';
    import APIBlock from './api_block.vue';
</script>

# HTTP API

The API exposes interface for managing your own pods and query server status.  
- HTTP method `GET` is used for querying data without side effects;  
- HTTP method `POST` is used for creating or updating data.
- All parameters are passed via query string in URLs.

::: tip
Here examples of API calls are provided using `curl` utility.  
For better readability, you can format the output using `python -m json.tool`:  
```sh
curl -s ... | python -m json.tool
```
:::

<template v-for="apiName in Object.keys(apiData)">

<APIBlock :api-name="apiName" :api-desc="apiData[apiName]">
<template v-if="apiData[apiName].example">

```sh-vue
{{`${apiData[apiName].example.input} `}}
```
</template>
</APIBlock>

</template>