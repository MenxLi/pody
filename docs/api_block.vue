<script setup lang="ts">
    import type { APIDescription } from './api_data';
    import { codeToHtml } from 'shiki';
    import { ref, defineProps } from 'vue';

    const props = defineProps<{
        apiDesc: APIDescription;
    }>();

    const codeToHtmlOptions = {
        lang: 'sh',
        theme: 'nord',
        fontSize: '14px',
        fontFamily: 'Fira Code',
        highlight: true,
    };

    const exampleCode = ref<string>('');
    const exampleCodeStr = `
${props.apiDesc.example.description ? `# ${props.apiDesc.example.description}` : ''}
${props.apiDesc.example.input}
${props.apiDesc.example.output ? `> ${props.apiDesc.example.output}` : ''}
    `;
    codeToHtml(exampleCodeStr, codeToHtmlOptions).then((html) => {
        exampleCode.value = html;
    });

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
                <div class="code-block" v-html="exampleCode"></div>
            </details>
        </div>
    </div>
</template>

<style scoped>
    .endpoint {
        color: var(--vp-c-brand);
    }

    .code-block {
        overflow-x: auto;
        border-radius: 1em;
        padding-inline: 1em;
        background-color: #2e3440;

        scrollbar-width: none;
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

</style>
