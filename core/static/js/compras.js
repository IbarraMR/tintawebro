document.addEventListener("DOMContentLoaded", () => {

    const tbody = document.querySelector("#detalle-body");
    const addBtn = document.querySelector("#add-row");
    const totalSpan = document.querySelector("#total-compra");
    const totalForms = document.querySelector("input[name='detallescompra_set-TOTAL_FORMS']");

    function recalcular() {
        let total = 0;

        document.querySelectorAll(".detalle-row").forEach(row => {
            const cantidadInput = row.querySelector("input[name*='cantidad']");
            const precioInput = row.querySelector("input[name*='precio_unitario']");
            const subtotalInput = row.querySelector(".subtotal-input");

            // Si falta algún campo clave, saltamos esta fila
            if (!cantidadInput || !precioInput || !subtotalInput) return;

            const cant = parseFloat(cantidadInput.value) || 0;
            const precio = parseFloat(precioInput.value) || 0;

            const sub = cant * precio;
            subtotalInput.value = sub.toFixed(2);

            total += sub;
        });

        totalSpan.textContent = total.toFixed(2);
    }

    function actualizarPrecioDesdeInsumo(row) {
        const selectInsumo = row.querySelector("select[name*='insumo']");
        const precioInput = row.querySelector("input[name*='precio_unitario']");
        
        if (selectInsumo && precioInput) {
            // Obtiene el precio del atributo data-precio del <option> seleccionado
            const precioInicial = selectInsumo.selectedOptions[0]?.dataset.precio || 0;
            
            // Solo actualiza el precio si el campo está vacío o en 0 (si se carga o si se cambia el insumo)
            if (precioInput.value === "" || parseFloat(precioInput.value) === 0) {
                 precioInput.value = parseFloat(precioInicial).toFixed(2);
            }
        }
        recalcular();
    }


    function conectar(row) {
        // Eventos de cálculo
        row.querySelector("input[name*='cantidad']")?.addEventListener("input", recalcular);
        row.querySelector("input[name*='precio_unitario']")?.addEventListener("input", recalcular);
        
        // Al cambiar el insumo, actualiza el precio (si el usuario no lo ha cambiado ya)
        row.querySelector("select[name*='insumo']")?.addEventListener("change", (e) => {
            actualizarPrecioDesdeInsumo(row);
        });

        // Conectar el botón de eliminar
        row.querySelector(".btn-eliminar")?.addEventListener("click", () => {
            const deleteCheckbox = row.querySelector("input[type='checkbox'][name*='DELETE']");

            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.style.display = "none";
                recalcular();
            } else {
                // Si la fila no es de Django, la eliminamos físicamente
                row.remove(); 
                recalcular();
            }
        });

        // Cargar el precio inicial del insumo al conectar (útil para filas cargadas inicialmente)
        actualizarPrecioDesdeInsumo(row);
    }

    // conectar eventos a filas existentes
    document.querySelectorAll(".detalle-row").forEach(conectar);

    addBtn.addEventListener("click", () => {
        const template = document.querySelector("#formset-empty")?.innerHTML;
        const index = totalForms.value;

        if (!template || !totalForms) return;

        const newRowHTML = template.replace(/__prefix__/g, index);
        tbody.insertAdjacentHTML("beforeend", newRowHTML);

        totalForms.value = Number(index) + 1;

        // Necesitamos encontrar la nueva fila dentro de la tabla después de la inserción
        const newRow = tbody.lastElementChild;
        if(newRow) {
            conectar(newRow);
        }
    });

    // Recalcular al inicio si hay datos precargados
    recalcular();
});
// static/js/compras.js

// Función Genérica para manejar el envío de formularios de modal por AJAX
function submitAjaxForm(formId, modalId, successCallback) {
    const form = document.getElementById(formId);
    const modalElement = document.getElementById(modalId);
    
    // Si el formulario no existe, salimos
    if (!form) return; 

    // Escucha el evento de envío del formulario
    form.addEventListener('submit', function(e) {
        e.preventDefault(); // Detiene el envío normal (recarga)
        
        const formData = new FormData(form);
        const actionUrl = form.getAttribute('action'); // Obtiene la URL de la vista AJAX
        
        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Ejecuta la función de éxito específica (p. ej., añadir al select)
                successCallback(data); 

                // Cierra el modal de Bootstrap
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }

                // Opcional: Limpia el formulario
                form.reset();
                
                // Muestra un mensaje de éxito (puedes usar messages de Django o JS)
                console.log('Registro guardado con éxito:', data.nombre);

            } else {
                // Manejar errores de validación del formulario
                alert('Error de validación: ' + JSON.stringify(data.errors));
            }
        })
        .catch(error => {
            console.error('Error en la solicitud AJAX:', error);
            alert('Ocurrió un error al intentar guardar el registro.');
        });
    });
}

// ===============================================
// LÓGICA ESPECÍFICA DE INICIALIZACIÓN
// ===============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ... (El resto de tu lógica de DOMContentLoaded, incluyendo la inicialización de formset) ...
    
    
    // --- MANEJO DE PROVEEDOR AJAX ---
    
    // Función de éxito para Proveedor
    const handleProveedorSuccess = (data) => {
        const proveedorSelect = document.querySelector('#id_proveedor'); // Asume que este es el ID del select principal
        
        // 1. Añade la nueva opción al select
        const newOption = new Option(data.nombre, data.id, true, true); 
        proveedorSelect.appendChild(newOption);
        
        // 2. Dispara un evento para actualizar el select visualmente si usas librerías
        proveedorSelect.dispatchEvent(new Event('change'));
    };

    // Inicializa el envío del formulario de Proveedor
    const proveedorFormModal = document.getElementById('proveedorFormModal');
    const proveedorModalElement = document.getElementById('proveedorModal');
    
    // Escucha el clic del botón 'Guardar' para disparar el submit del formulario oculto
    document.getElementById('btnGuardarProveedor').addEventListener('click', function() {
        if (proveedorFormModal) {
            proveedorFormModal.dispatchEvent(new Event('submit')); // Dispara el submit
        }
    });

    // Configura la lógica de envío
    submitAjaxForm('proveedorFormModal', 'proveedorModal', handleProveedorSuccess);


    // --- MANEJO DE INSUMO AJAX ---

    // Función de éxito para Insumo
    const handleInsumoSuccess = (data) => {
        // En un caso real, necesitarías encontrar el select correcto del formset
        const primerInsumoSelect = document.querySelector('.detalle-insumo'); 
        
        // 1. Añade la nueva opción
        const newOption = new Option(data.nombre, data.id, true, true);
        primerInsumoSelect.appendChild(newOption);
        
        // 2. Actualiza la variable global de precios (CRUCIAL para el cálculo)
        if (typeof INSUMO_PRECIOS !== 'undefined') {
            INSUMO_PRECIOS[data.id] = data.precio_costo_unitario;
        }

        primerInsumoSelect.dispatchEvent(new Event('change'));
    };
    
    // Configura la lógica de envío (si tienes el form de insumo implementado)
    // submitAjaxForm('insumoFormModal', 'insumoModal', handleInsumoSuccess); 
    // ... (Debes implementar el botón y el evento para Insumo de forma similar)

});

// ... (Resto de funciones como calcularSubtotal, etc.)