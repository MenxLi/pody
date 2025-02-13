<script setup lang="ts">
    import { APIDescription } from './api_data';

    const props = defineProps<{
        apiData: { [key: string]: APIDescription };
    }>();
</script>

<template>
    <div id="table-container">
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
                    <div class="single-line">
                        {{ apiName }}
                    </div>
                </a></td>
                <td>{{ props.apiData[apiName].method }}</td>
                <td><div class='single-line'>
                    {{ Object.keys(props.apiData[apiName].parameters || {}).join(', ') }}
                </div></td>
            </tr>
        </tbody>
    </table>
    </div>
</template>

<style scoped>
    #table-container {
        overflow-x: auto;
        display: flex;
    }
    table{
        width: 100% !important;
    }
    thead > tr > th:last-child {
        /* background-color: red !important; */
        width: 100%;
    }
    .single-line {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>