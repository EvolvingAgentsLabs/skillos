<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { skillHostBridge } from "$lib/skills/skill_host_bridge";

  let iframeEl: HTMLIFrameElement | null = $state(null);

  onMount(() => {
    if (iframeEl) skillHostBridge.attachIframe(iframeEl);
  });

  onDestroy(() => {
    skillHostBridge.detach();
  });
</script>

<iframe
  bind:this={iframeEl}
  src="/iframe/skill-host.html"
  title="SkillOS skill host"
  sandbox="allow-scripts"
  aria-hidden="true"
  tabindex="-1"
></iframe>

<style>
  iframe {
    position: fixed;
    width: 0;
    height: 0;
    border: none;
    opacity: 0;
    pointer-events: none;
    left: -9999px;
    top: -9999px;
  }
</style>
