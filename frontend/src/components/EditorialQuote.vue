<script setup lang="ts">
interface Props {
  cite?: string
}
defineProps<Props>()
</script>

<template>
  <blockquote class="editorial-quote">
    <slot />
    <cite v-if="cite">{{ cite }}</cite>
  </blockquote>
</template>
