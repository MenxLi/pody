<script setup lang="ts">
    import { APIDescription } from './api_data';

    const props = defineProps<{
        apiData: { [key: string]: APIDescription };
    }>();
</script>

<template>
    <table>
        <thead>
            <tr>
                <th>API</th>
                <th>Method</th>
                <th>Params</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="apiName in Object.keys(props.apiData)" :key="apiName">
                <td><a v-bind:href="`#${apiName.replace(/[\s\/]/g, '-').slice(1)}`">
                   {{ apiName }}
                </a></td>
                <td>{{ props.apiData[apiName].method }}</td>
                <td>{{ Object.keys(props.apiData[apiName].parameters || {}).join(', ') }}</td>
            </tr>
        </tbody>
    </table>
</template>