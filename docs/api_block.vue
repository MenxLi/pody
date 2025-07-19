<script setup lang="ts">
    import type { APIDescription } from './api_data';
    import { defineProps } from 'vue';

    const props = defineProps<{
        apiName: string;
        apiDesc: APIDescription;
    }>();

    const id = props.apiName.replace(/[\s\/]/g, '-').slice(1);

</script>

<template>
    <div>
        <hr>
        <h3 :id=id>{{ props.apiName }}</h3>
        <p class="compact" style="margin-bottom: 0.2rem"><span :class="`api-method ${props.apiDesc.method}`"
            >{{ props.apiDesc.method }}</span>{{ props.apiDesc.description }}</p>
        <div class="detail-block">
            <div class="compact" v-if="props.apiDesc.parameters && Object.keys(props.apiDesc.parameters).length > 0">
                <i>Parameters</i>
                <ul>
                    <li v-for="paramName in Object.keys(props.apiDesc.parameters)">
                        <span :class="'params'">
                            <strong>{{ paramName }}</strong> [{{ props.apiDesc.parameters[paramName].type }}] 
                            <span v-if="props.apiDesc.parameters[paramName].optional" class="optional">optional</span>
                        </span>{{ props.apiDesc.parameters[paramName].description }}
                    </li>
                </ul>
            </div>
            <details class="compact" v-if="props.apiDesc.example">
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
    h3 {
        color: var(--vp-c-brand);
    }
    p{
        vertical-align: middle;
    }
    span.api-method, span.params {
        font-weight: bold;
        font-size: small;
        padding: 0.2em 0.5em;
        background-color: var(--vp-code-bg);
        margin-right: 0.5em;
        border-radius: 0.2em;
    }
    .api-method.GET{ color: var(--vp-c-green-1); }
    .api-method.POST{ color: var(--vp-c-yellow-1); }
    span.params {
        font-weight: unset;
        color: var(--vp-c-text-1);
    }

    span.optional {
        color: var(--vp-c-text-3);
        margin-left: 0.5em;
    }

    .detail-block {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
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
        padding: 0.5em;
        font-size: small;
        display: block;
        overflow: auto;
        background-color: var(--vp-code-bg);
    }

</style>
