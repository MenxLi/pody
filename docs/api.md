---
outline: deep
---

<script setup lang="ts">
    import apiData from './api_data.ts';
    import APIBlock from './api_block.vue';
</script>

# HTTP API

<template v-for="apiName in Object.keys(apiData)">

## {{ apiName }}
<APIBlock :api-desc="apiData[apiName]">

```sh-vue
{{`${apiData[apiName].example.input} `}}
```
</APIBlock>

</template>

<style scoped>
    h2 {
        color: var(--vp-c-brand);
    }
</style>
