(function() {
    'use strict';

    function initWidget(container) {
        const fieldId = container.id.replace('specifications-widget-', '');
        const hiddenInput = document.getElementById('id_' + fieldId);
        const tableBody = container.querySelector('tbody');
        const addButton = container.querySelector('#add-spec-row-' + fieldId);

        function updateHiddenInput() {
            const specs = {};
            const rows = tableBody.querySelectorAll('.spec-row');
            rows.forEach(row => {
                const key = row.querySelector('.spec-key').value.trim();
                const val = row.querySelector('.spec-value').value.trim();
                if (key) {
                    specs[key] = val;
                }
            });
            hiddenInput.value = JSON.stringify(specs);
        }

        addButton.addEventListener('click', function() {
            const row = document.createElement('tr');
            row.className = 'spec-row';
            row.innerHTML = `
                <td><input type="text" class="form-control form-control-sm spec-key" value=""></td>
                <td><input type="text" class="form-control form-control-sm spec-value" value=""></td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-spec-row">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
            
            row.querySelector('.remove-spec-row').addEventListener('click', function() {
                row.remove();
                updateHiddenInput();
            });

            row.querySelectorAll('input').forEach(input => {
                input.addEventListener('input', updateHiddenInput);
            });
        });

        // Initialize existing rows
        tableBody.querySelectorAll('.spec-row').forEach(row => {
            row.querySelector('.remove-spec-row').addEventListener('click', function() {
                row.remove();
                updateHiddenInput();
            });

            row.querySelectorAll('input').forEach(input => {
                input.addEventListener('input', updateHiddenInput);
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.specifications-widget').forEach(initWidget);
    });
})();
