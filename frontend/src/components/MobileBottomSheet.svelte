<script>
  let {
    open = false,
    expanded = $bindable(false),
    onClose = () => {},
    peekContent,
    children
  } = $props();

  let startY = 0;
  let startTime = 0;
  let dragOffset = $state(0);
  let dragging = $state(false);

  const PEEK_HEIGHT = 180;
  const SHEET_HEIGHT_VH = 80;
  const HANDLE_ZONE = 48; // px from top of sheet that initiates drag

  // When closed, reset expanded + drag
  $effect(() => {
    if (!open) {
      expanded = false;
      dragOffset = 0;
      dragging = false;
    }
  });

  function handleTouchStart(e) {
    // Only allow drag from the handle zone (top ~48px of sheet)
    const sheetEl = e.currentTarget;
    const rect = sheetEl.getBoundingClientRect();
    const touchY = e.touches[0].clientY;
    if (touchY - rect.top > HANDLE_ZONE) return;

    startY = e.touches[0].clientY;
    startTime = Date.now();
    dragging = true;
    dragOffset = 0;
  }

  function handleTouchMove(e) {
    if (!dragging) return;
    const currentY = e.touches[0].clientY;
    const delta = currentY - startY;

    if (expanded) {
      // In expanded state: only allow dragging downward (positive delta)
      dragOffset = Math.max(0, delta);
    } else {
      // In peek state: allow dragging up (negative) or down (positive)
      dragOffset = delta;
    }
  }

  function handleTouchEnd() {
    if (!dragging) return;
    dragging = false;

    const elapsed = Date.now() - startTime;
    const velocity = dragOffset / Math.max(elapsed, 1); // px/ms

    if (expanded) {
      // Expanded → decide collapse or stay
      if (velocity > 0.4 || dragOffset > 120) {
        // Fast swipe down or large drag → collapse to peek
        expanded = false;
      }
    } else {
      // Peek state
      if (velocity < -0.3 || dragOffset < -60) {
        // Fast swipe up or drag up → expand
        expanded = true;
      } else if (velocity > 0.3 || dragOffset > 60) {
        // Fast swipe down or drag down → close
        expanded = false;
        onClose();
      }
    }

    dragOffset = 0;
  }

  // Compute the translateY value
  const restTranslate = $derived(
    expanded ? 0 : `calc(${SHEET_HEIGHT_VH}vh - ${PEEK_HEIGHT}px)`
  );
</script>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed left-0 right-0 z-[999] rounded-t-xl"
    class:will-change-transform={dragging}
    style="
      bottom: calc(56px + env(safe-area-inset-bottom, 0px));
      height: {SHEET_HEIGHT_VH}vh;
      transform: translateY({typeof restTranslate === 'number' ? `${restTranslate + dragOffset}px` : `calc(${restTranslate} + ${dragOffset}px)`});
      transition: {dragging ? 'none' : 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)'};
      background: {expanded ? '#0d1117' : '#0d1117'};
      border-top: 1px solid #1e2a3a;
      box-shadow: {expanded ? '0 -8px 32px rgba(0,0,0,0.6)' : '0 -4px 16px rgba(0,0,0,0.3)'};
    "
    ontouchstart={handleTouchStart}
    ontouchmove={handleTouchMove}
    ontouchend={handleTouchEnd}
  >
    <!-- Drag handle -->
    <div class="flex flex-col items-center pt-2 pb-1 cursor-grab">
      <div class="w-9 h-1 rounded-full bg-[#3a4a5a]"></div>
      <!-- Chevron hint in peek state -->
      {#if !expanded}
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="#5a6a7a" stroke-width="2"
          class="mt-0.5 opacity-60"
        >
          <path d="M18 15l-6-6-6 6"/>
        </svg>
      {/if}
    </div>

    <!-- Content -->
    <div
      class="overflow-y-auto px-4 pb-6"
      style="height: calc(100% - {expanded ? '24px' : '36px'}); overscroll-behavior: contain;"
    >
      {#if !expanded && peekContent}
        {@render peekContent()}
      {:else if children}
        {@render children()}
      {/if}
    </div>
  </div>
{/if}
