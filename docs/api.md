---
outline: deep
---

<script setup lang="ts">
    import apiData from './api_data.ts';
    import APIBlock from './api_block.vue';
    console.log(apiData);
</script>

# HTTP API

<template v-for="apiName in Object.keys(apiData)">

## {{ apiName }}

<APIBlock :api-desc="apiData[apiName]" />
</template>

<style scoped>
    h2 {
        color: var(--vp-c-brand);
    }
</style>
