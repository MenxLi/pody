<script setup lang="ts">
    import type { APIDescription } from './api_data';
    import { ref, defineProps } from 'vue';

    const props = defineProps<{
        apiDesc: APIDescription;
    }>();

</script>

<template>
    <div>
        <p>{{ props.apiDesc.description }}</p>
        <div class="detail-block">
            <details class="compact">
                <summary class="compact">Parameters</summary>
                <ul>
                    <li v-for="paramName in Object.keys(props.apiDesc.parameters)">
                        <strong>{{ paramName }}</strong> [{{ props.apiDesc.parameters[paramName].type }}] - {{ props.apiDesc.parameters[paramName].description }}
                    </li>
                </ul>
            </details>
            <details class="compact">
                <summary class="compact">Example</summary>
                <div v-if="props.apiDesc.example.description">
                    <code class="example-desc" >{{ props.apiDesc.example.description }}</code>
                </div>
                <!-- Put the example code in the slot with markdown -->
                <slot></slot>
                <div class="example-output" v-if="props.apiDesc.example.output">
                    <code class="example-output">> {{ props.apiDesc.example.output }}</code>
                </div>
            </details>
        </div>
    </div>
</template>

<style scoped>
    .detail-block {
        display: flex;
        flex-direction: column;
        gap: 1em;
    }

    .compact {
        margin: 0em;
        padding: 0em;
    }

    code.example-desc {
        display: block;
        padding: 0.5em;
    }

</style>
