<script lang="ts">
  /**
   * OfflineBanner — inverted-expectation UX for a local-first app.
   *
   * Most apps treat "offline" as degraded mode. SkillOS's positioning is
   * the opposite: offline is when the write-once/run-forever-locally loop
   * pays off. When connectivity drops we actively reassure the user that
   * local recipes still run (free, private, deterministic), and note that
   * any cloud-assisted synthesis will be unavailable until reconnected.
   */
  import { onMount } from "svelte";

  let online = $state(true);

  onMount(() => {
    online = navigator.onLine;
    const up = () => (online = true);
    const down = () => (online = false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  });
</script>

{#if !online}
  <div class="banner" role="status" aria-live="polite">
    <span class="ico" aria-hidden="true">⚡</span>
    <span class="text">
      Offline — local recipes still run. Cloud synthesis paused.
    </span>
  </div>
{/if}

<style>
  .banner {
    position: fixed;
    top: env(safe-area-inset-top, 0);
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    padding: 0.4rem 0.8rem;
    background: color-mix(in srgb, var(--ok) 14%, var(--bg-2));
    border-bottom: 1px solid color-mix(in srgb, var(--ok) 40%, var(--border));
    color: var(--fg);
    font-size: 0.78rem;
    z-index: 10;
    font-weight: 500;
  }
  .ico {
    color: var(--ok);
    font-size: 0.95rem;
    line-height: 1;
  }
  .text {
    text-align: center;
  }
</style>
