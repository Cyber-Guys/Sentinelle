// Senza profilo si passa dal benvenuto (nome e telefono, oppure un profilo demo).
export default defineNuxtRouteMiddleware((a) => {
  if (a.path === '/benvenuto') return
  if (!useSessione().id.value) return navigateTo('/benvenuto')
})
