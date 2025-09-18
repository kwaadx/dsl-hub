<script setup lang="ts">
import {ref} from 'vue';

const year = ref(new Date().getFullYear());
</script>

<template>
  <footer
    class="bg-white dark:bg-neutral-800 flex justify-center text-xs text-neutral-500 w-full p-3">
    © {{ year }} DSL Hub
  </footer>
</template>


<!--<script type="text/javascript">-->
<!--window.turnOfClickToRedirectLink = true-->
<!--</script>-->
<!--&lt;!&ndash; Hotjar Tracking Code for FixPulse &ndash;&gt;-->
<!--<script>-->
<!--(function(h,o,t,j,a,r){-->
<!--  h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};-->
<!--  h._hjSettings={hjid:6519636,hjsv:6};-->
<!--  a=o.getElementsByTagName('head')[0];-->
<!--  r=o.createElement('script');r.async=1;-->
<!--  r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;-->
<!--  a.appendChild(r);-->
<!--})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');-->
<!--</script>-->
<!--<script>-->
<!--gtag('config', 'AW-16542885709/D9fvCIaFpqEaEM3OodA9', {-->
<!--  phone_conversion_number: '(224) 808-3098',-->
<!--  phone_conversion_callback: function(formatted, mobileNumber) {-->
<!--    document.querySelectorAll('body *').forEach(function(node) {-->
<!--      if (node.children.length === 0 && node.textContent.includes('(224) 808-3098')) {-->
<!--        node.textContent = node.textContent.replace('(224) 808-3098', formatted);-->
<!--      }-->
<!--    });-->

<!--    document.querySelectorAll('a[href^="tel:"]').forEach(function(a) {-->
<!--      if (a.href.includes('2248083098')) {-->
<!--        a.href = 'tel:' + mobileNumber;-->
<!--      }-->
<!--    });-->
<!--  }-->
<!--});-->
<!--</script>-->
