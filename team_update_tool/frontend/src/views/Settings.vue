<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Settings</h2>
    <div class="grid grid-cols-1 gap-4 max-w-2xl">
      <div class="card p-5">
        <h3 class="font-semibold text-gray-900 mb-4">Notification Preferences</h3>
        <label class="flex items-center gap-3 mb-3"><input type="checkbox" checked class="rounded border-gray-300 text-green-600" /><span class="text-sm">Email notifications for new tasks</span></label>
        <label class="flex items-center gap-3 mb-3"><input type="checkbox" checked class="rounded border-gray-300 text-green-600" /><span class="text-sm">Email notifications for status changes</span></label>
        <label class="flex items-center gap-3"><input type="checkbox" class="rounded border-gray-300 text-green-600" /><span class="text-sm">Weekly digest email</span></label>
      </div>
    </div>
  </div>
</template>
