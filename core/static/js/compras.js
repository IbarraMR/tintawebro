console.log("✅ compras.js cargado correctamente");

function validarFormulario() {
    const registrarBtn = document.querySelector("button[type='submit']");
    const proveedor = document.querySelector("#id_proveedor").value;
    const empleado = document.querySelector("#id_empleado").value;
    const formaPago = document.querySelector("#id_forma_pago").value;

    let valido = proveedor && empleado && formaPago;

    document.querySelectorAll(".detalle-row").forEach(row => {
        const insumo = row.querySelector(".detalle-insumo")?.value;
        const cantidad = parseFloat(row.querySelector(".detalle-cantidad")?.value);
        const precio = parseFloat(row.querySelector(".detalle-precio")?.value);
        const deleteInput = row.querySelector("input[name*='DELETE']");

        if (deleteInput?.checked) return; // ignorar filas marcadas para borrar

        if (!insumo || isNaN(cantidad) || cantidad <= 0 || isNaN(precio) || precio <= 0) {
            valido = false;
        }
    });

    registrarBtn.disabled = !valido;
}


function actualizarTotal() {
    let total = 0;

    document.querySelectorAll('.detalle-subtotal').forEach(input => {
        const row = input.closest('.detalle-row');
        const deleteInput = row?.querySelector("input[name*='DELETE']");
        const isDeleted = deleteInput?.checked ?? false;

        if (!isDeleted) {
            total += parseFloat(input.value) || 0;
        }
    });

    document.querySelector("#total-compra").innerText = total.toFixed(2);
    validarFormulario();
}


function calcularSubtotal(row) {
    const insumoSelect = row.querySelector(".detalle-insumo");
    const cantidadInput = row.querySelector(".detalle-cantidad");
    const precioInput = row.querySelector(".detalle-precio");
    const subtotalInput = row.querySelector(".detalle-subtotal");

    const insumoId = insumoSelect.value;
    let cantidad = parseFloat(cantidadInput.value) || 0;
    let precio = parseFloat(precioInput.value) || 0;

    if (cantidad <= 0) {
        cantidad = 1;
        cantidadInput.value = 1;
    }

    if (precio <= 0 && INSUMO_PRECIOS[insumoId]) {
        precio = parseFloat(INSUMO_PRECIOS[insumoId]);
        precioInput.value = precio.toFixed(2);
    }

    subtotalInput.value = (cantidad * precio).toFixed(2);

    actualizarTotal();
}


function conectarEventosFila(row) {
    const insumo = row.querySelector(".detalle-insumo");
    const cantidad = row.querySelector(".detalle-cantidad");
    const precio = row.querySelector(".detalle-precio");
    const deleteBtn = row.querySelector(".btn-eliminar");

    if (cantidad && cantidad.value === "") cantidad.value = 1;

    if (insumo) insumo.addEventListener("change", () => calcularSubtotal(row));
    if (cantidad) cantidad.addEventListener("input", () => calcularSubtotal(row));
    if (precio) precio.addEventListener("input", () => calcularSubtotal(row));

    if (deleteBtn) {
        deleteBtn.addEventListener("click", () => {
            const deleteInput = row.querySelector("input[name*='DELETE']");
            if (deleteInput) deleteInput.checked = true;
            row.style.display = "none";
            actualizarTotal();
        });
    }

    calcularSubtotal(row);
}


document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 DOM cargado, conectando filas...");

    document.querySelectorAll(".detalle-row").forEach(conectarEventosFila);
    actualizarTotal(); 

    const addRowButton = document.getElementById("add-row");
    const totalForms = document.querySelector("input[name$='TOTAL_FORMS']");
    const tbody = document.getElementById("detalle-body");
    const template = document.getElementById("formset-empty");

    if (addRowButton) {
        addRowButton.addEventListener("click", () => {
            let formIndex = Number(totalForms.value);
            let newRowHtml = template.innerHTML.replace(/__prefix__/g, formIndex);

            tbody.insertAdjacentHTML("beforeend", newRowHtml);

            const newRow = tbody.lastElementChild;
            conectarEventosFila(newRow);

            totalForms.value = formIndex + 1;
        });
    }

    function submitAjaxForm(formId, modalId, successCallback) {
        const form = document.getElementById(formId);
        const modalEl = document.getElementById(modalId);

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        alert("⚠ Error: " + JSON.stringify(data.errors));
                        return;
                    }

                    successCallback(data);

                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();
                    form.reset();
                })
                .catch(err => console.error(err));
        });
    }

    submitAjaxForm("insumoFormModal", "insumoModal", (data) => {
        INSUMO_PRECIOS[data.id] = parseFloat(data.precio_costo_unitario);

        const lastRow = document.querySelector("#detalle-body").lastElementChild;
        const select = lastRow.querySelector(".detalle-insumo");

        const option = new Option(data.nombre, data.id, true, true);
        select.appendChild(option);

        calcularSubtotal(lastRow);
    });

    document.getElementById("btnGuardarInsumo").addEventListener("click", function () {
        document.getElementById("insumoFormModal").dispatchEvent(new Event("submit"));
    });

    document.addEventListener("click", function (e) {
        if (e.target.closest("[data-bs-target='#insumoModal']")) {
            const proveedorCompra = document.querySelector("#id_proveedor");
            const proveedorModal = document.querySelector("#id_proveedor_modal");

            if (proveedorCompra && proveedorModal) {
                proveedorModal.value = proveedorCompra.value;
            }
        }
    });
});
