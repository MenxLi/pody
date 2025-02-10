<script setup lang="ts">
    import type { APIDescription } from './api_data';
    import { defineProps } from 'vue';

    const props = defineProps<{
        apiDesc: APIDescription;
    }>();

</script>

<template>
    <div>
        <p><span class="api-method">{{ props.apiDesc.method }}</span>{{ props.apiDesc.description }}</p>
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
                    <i>Output:</i>
                    <pre><code class="example-output">{{ props.apiDesc.example.output }}</code></pre> 
                </div>
            </details>
        </div>
    </div>
</template>

<style scoped>
    p{
        vertical-align: middle;
    }
    span.api-method {
        color: var(--vp-c-green-1);
        font-weight: bold;
        font-size: small;
        padding: 0.2em 0.5em;
        background-color: var(--vp-code-bg);
        margin-right: 0.5em;
        border-radius: 0.2em;
    }

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

    code.example-output {
        font-size: x-small;
        display: block;
        overflow: auto;
        background-color: var(--vp-code-bg);
    }

</style>
