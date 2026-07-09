/** 表单工具函数. */

export function showFieldError(input, message) {
  clearFieldError(input);
  const error = document.createElement('span');
  error.className = 'field-error';
  error.textContent = message;
  input.parentElement.appendChild(error);
  input.classList.add('input-error');
}

export function clearFieldError(input) {
  const existing = input.parentElement.querySelector('.field-error');
  if (existing) existing.remove();
  input.classList.remove('input-error');
}

export function clearAllErrors(form) {
  form.querySelectorAll('.field-error').forEach(e => e.remove());
  form.querySelectorAll('.input-error').forEach(e => e.classList.remove('input-error'));
}
