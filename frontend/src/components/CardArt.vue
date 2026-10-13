<script setup>
// Small original illustrations for the front-page cards. They are drawn with the card's own orange shade
// (--tone, --tone-soft, --tone-text), so each one matches its card and a white-label brand colour carries through.
defineProps({ name: { type: String, required: true } })
</script>

<template>
  <svg class="card-art" viewBox="0 0 120 70" role="presentation" aria-hidden="true" focusable="false">
    <rect x="0" y="0" width="120" height="70" rx="10" class="art-bg" />

    <!-- Revenue: waits (clock + bars) -->
    <g v-if="name === 'waits'">
      <circle cx="40" cy="35" r="20" class="art-fill art-line" />
      <path d="M40 22v14l9 6" class="art-line art-nofill" />
      <rect x="70" y="40" width="9" height="16" rx="2" class="art-solid art-faint" />
      <rect x="82" y="26" width="9" height="30" rx="2" class="art-solid" />
      <rect x="94" y="34" width="9" height="22" rx="2" class="art-solid art-faint" />
    </g>
    <!-- themes: the same speech bubble repeating -->
    <g v-else-if="name === 'themes'">
      <rect x="14" y="12" width="48" height="26" rx="8" class="art-fill art-line" />
      <path d="M26 38l-2 9 11-9" class="art-fill art-line" />
      <rect x="52" y="30" width="48" height="26" rx="8" class="art-solid" />
      <path d="M86 56l4 8-13-8" class="art-solid" />
      <path d="M62 43h28M62 49h18" stroke="#fff" stroke-width="3" stroke-linecap="round" />
      <path d="M24 22h28M24 28h16" class="art-line art-nofill" />
    </g>
    <!-- drift: a line sliding down -->
    <g v-else-if="name === 'drift'">
      <path d="M14 56h92M14 14v42" class="art-line art-nofill art-faint" />
      <path d="M18 22l20 6 18-2 18 14 22 8" class="art-line art-nofill art-thick" />
      <circle cx="94" cy="48" r="5" class="art-solid" />
    </g>
    <!-- locations: pins on a map -->
    <g v-else-if="name === 'locations'">
      <path d="M12 54l22-10 24 8 24-12 24 8" class="art-line art-nofill art-faint" />
      <path d="M36 44c-8-10-12-14-12-20a12 12 0 0 1 24 0c0 6-4 10-12 20z" class="art-solid" />
      <circle cx="36" cy="24" r="4.5" fill="#fff" />
      <path d="M84 38c-5-6-7-9-7-13a7 7 0 0 1 14 0c0 4-2 7-7 13z" class="art-fill art-line" />
      <circle cx="84" cy="25" r="2.5" class="art-solid" />
    </g>
    <!-- followup: an inbox with a tick -->
    <g v-else-if="name === 'followup'">
      <rect x="22" y="16" width="62" height="40" rx="6" class="art-fill art-line" />
      <path d="M22 24l31 20 31-20" class="art-line art-nofill" />
      <circle cx="88" cy="46" r="15" class="art-solid" />
      <path d="M80 46l6 6 11-12" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
    </g>
    <!-- platforms: overlapping review cards telling different stories -->
    <g v-else-if="name === 'platforms'">
      <rect x="12" y="16" width="40" height="34" rx="6" class="art-fill art-line" />
      <rect x="40" y="22" width="40" height="34" rx="6" class="art-fill art-line" />
      <rect x="68" y="12" width="40" height="34" rx="6" class="art-solid" />
      <path d="M78 24l3 7 7-6M78 38h20" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" />
      <path d="M50 34h20M50 42h12" class="art-line art-nofill" />
    </g>

    <!-- Roles: owner (storefront) -->
    <g v-else-if="name === 'owner'">
      <path d="M22 28l6-14h64l6 14z" class="art-solid" />
      <rect x="26" y="28" width="68" height="28" class="art-fill art-line" />
      <rect x="52" y="36" width="16" height="20" rx="2" class="art-solid art-faint" />
      <path d="M22 28c0 5 8 5 8 0 0 5 10 5 10 0 0 5 10 5 10 0 0 5 10 5 10 0 0 5 10 5 10 0 0 5 8 5 8 0" class="art-line art-nofill" />
    </g>
    <!-- operations (route between places) -->
    <g v-else-if="name === 'operations'">
      <path d="M26 50C26 30 52 44 60 30S88 28 94 20" class="art-line art-nofill art-thick" stroke-dasharray="2 6" />
      <circle cx="26" cy="50" r="8" class="art-solid" />
      <circle cx="60" cy="31" r="8" class="art-fill art-line" />
      <circle cx="94" cy="20" r="8" class="art-solid" />
    </g>
    <!-- marketing (megaphone) -->
    <g v-else-if="name === 'marketing'">
      <path d="M30 28h14l30-14v42L44 42H30z" class="art-solid" />
      <rect x="22" y="28" width="10" height="14" rx="3" class="art-fill art-line" />
      <path d="M38 42l4 14h8l-4-14" class="art-fill art-line" />
      <path d="M84 26c5 4 5 14 0 18M92 20c9 8 9 22 0 30" class="art-line art-nofill art-thick" />
    </g>
    <!-- experience (heart in a speech bubble) -->
    <g v-else-if="name === 'experience'">
      <rect x="24" y="12" width="72" height="40" rx="12" class="art-fill art-line" />
      <path d="M42 52l-4 11 16-11" class="art-fill art-line" />
      <path d="M60 42c-14-9-15-18-8-21 4-1.5 7 .5 8 3 1-2.500 4-4.500 8-3 7 3 6 12-8 21z" class="art-solid" />
    </g>
    <!-- location (building with a pin) -->
    <g v-else-if="name === 'location'">
      <rect x="22" y="22" width="34" height="36" rx="3" class="art-fill art-line" />
      <rect x="62" y="34" width="26" height="24" rx="3" class="art-fill art-line" />
      <path d="M30 32h6M42 32h6M30 42h6M42 42h6M70 44h4M78 44h4" class="art-line art-nofill" />
      <path d="M96 30c-6-7-8-10-8-14a8 8 0 0 1 16 0c0 4-2 7-8 14z" class="art-solid" />
      <circle cx="96" cy="16" r="3" fill="#fff" />
    </g>
    <!-- leadership (bars with a trend) -->
    <g v-else-if="name === 'leadership'">
      <rect x="22" y="38" width="14" height="18" rx="2" class="art-solid art-faint" />
      <rect x="42" y="28" width="14" height="28" rx="2" class="art-solid art-faint" />
      <rect x="62" y="20" width="14" height="36" rx="2" class="art-solid" />
      <rect x="82" y="12" width="14" height="44" rx="2" class="art-solid" />
      <path d="M22 30l22-8 20-4 30-8" class="art-line art-nofill" />
    </g>
  </svg>
</template>

<style>
.card-art {
  display: block;
  width: 100%;
  max-width: 220px;
  height: auto;
  margin: 0 auto 4px;
}
.card-art .art-bg { fill: var(--tone-soft); }
.card-art .art-fill { fill: #fff; }
.card-art .art-solid { fill: var(--tone); }
.card-art .art-faint { opacity: 0.45; }
.card-art .art-line { stroke: var(--tone-text); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.card-art .art-nofill { fill: none; }
.card-art .art-thick { stroke-width: 3.5; }
</style>
