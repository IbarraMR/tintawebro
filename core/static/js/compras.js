console.log("✅ compras.js cargado correctamente");

function validarFormulario() {
    const registrarBtn = document.querySelector("button[type='submit']");
    if (!registrarBtn) return;

    const proveedor = document.querySelector("#id_proveedor")?.value || "";
    const formaPago = document.querySelector("#id_forma_pago")?.value || "";

    let valido = !!(proveedor && formaPago);

    document.querySelectorAll(".detalle-row").forEach(row => {
        const insumo = row.querySelector(".detalle-insumo")?.value;
        const cantidad = parseFloat(row.querySelector(".detalle-cantidad")?.value);
        const precio = parseFloat(row.querySelector(".detalle-precio")?.value);
        const deleteInput = row.querySelector("input[name*='DELETE']");

        if (deleteInput?.checked) return; 

        if (!insumo || isNaN(cantidad) || cantidad <= 0 || isNaN(precio) || precio <= 0) {
            valido = false;
        }
    });

    registrarBtn.disabled = !valido;
}

function actualizarTotal() {
    let total = 0;

    document.querySelectorAll(".detalle-subtotal").forEach(input => {
        const row = input.closest(".detalle-row");
        const deleteInput = row?.querySelector("input[name*='DELETE']");
        const isDeleted = deleteInput?.checked ?? false;

        if (!isDeleted) {
            total += parseFloat(input.value) || 0;
        }
    });

    const totalSpan = document.querySelector("#total-compra");
    if (totalSpan) totalSpan.innerText = total.toFixed(2);

    validarFormulario();
}

function calcularSubtotal(row) {
    const insumoSelect = row.querySelector(".detalle-insumo");
    const cantidadInput = row.querySelector(".detalle-cantidad");
    const precioInput = row.querySelector(".detalle-precio");
    const subtotalInput = row.querySelector(".detalle-subtotal");

    if (!insumoSelect || !cantidadInput || !precioInput || !subtotalInput) return;

    const insumoId = insumoSelect.value;
    let cantidad = parseFloat(cantidadInput.value) || 0;
    let precio = parseFloat(precioInput.value) || 0;

    if (cantidad <= 0) {
        cantidad = 1;
        cantidadInput.value = 1;
    }

    if (precio <= 0 && typeof INSUMO_PRECIOS !== "undefined" && INSUMO_PRECIOS[insumoId]) {
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

    insumo?.addEventListener("change", () => calcularSubtotal(row));
    cantidad?.addEventListener("input", () => calcularSubtotal(row));
    precio?.addEventListener("input", () => calcularSubtotal(row));

    deleteBtn?.addEventListener("click", () => {
        const deleteInput = row.querySelector("input[name*='DELETE']");
        if (deleteInput) deleteInput.checked = true;
        row.style.display = "none";
        actualizarTotal();
    });

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

    if (addRowButton && totalForms && tbody && template) {
        addRowButton.addEventListener("click", () => {
            const formIndex = Number(totalForms.value);
            const newRowHtml = template.innerHTML.replace(/__prefix__/g, formIndex);

            tbody.insertAdjacentHTML("beforeend", newRowHtml);
            const newRow = tbody.lastElementChild;
            conectarEventosFila(newRow);

            totalForms.value = formIndex + 1;
        });
    }

    const formInsumo = document.getElementById("insumoFormModal");
    const modalInsumoEl = document.getElementById("insumoModal");

    if (formInsumo && modalInsumoEl) {
        formInsumo.addEventListener("submit", function (e) {
            e.preventDefault();

            const datos = new FormData(formInsumo);

            fetch(formInsumo.action, {
                method: "POST",
                body: datos,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        alert("⚠ Error al guardar insumo: " + (data.message || JSON.stringify(data.errors)));
                        return;
                    }

                    if (typeof INSUMO_PRECIOS !== "undefined") {
                        INSUMO_PRECIOS[data.id] = parseFloat(data.precio_costo_unitario);
                    }

                    const lastRow = tbody.lastElementChild;
                    if (lastRow) {
                        const select = lastRow.querySelector(".detalle-insumo");
                        if (select) {
                            const option = new Option(data.nombre, data.id, true, true);
                            select.appendChild(option);
                        }
                        calcularSubtotal(lastRow);
                    }

                    const modal = bootstrap.Modal.getInstance(modalInsumoEl);
                    modal?.hide();
                    formInsumo.reset();
                })
                .catch(err => {
                    console.error("Error AJAX insumo:", err);
                    alert("Error inesperado al crear el insumo.");
                });
        });
    }

    document.addEventListener("click", (e) => {
        const trigger = e.target.closest("[data-bs-target='#insumoModal']");
        if (!trigger) return;

        const proveedorPrincipal = document.querySelector("#id_proveedor");
        const proveedorModal = document.querySelector("#insumoModal select[name='proveedor']");

        if (proveedorPrincipal && proveedorModal) {
            proveedorModal.value = proveedorPrincipal.value;
        }
    });

    const formProveedor = document.getElementById("proveedorFormModal");
    const modalProveedorEl = document.getElementById("proveedorModal");

    if (formProveedor && modalProveedorEl) {
        formProveedor.addEventListener("submit", function (e) {
            e.preventDefault();

            const datos = new FormData(formProveedor);

            fetch(formProveedor.action, {
                method: "POST",
                body: datos,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        alert("⚠ Error al guardar proveedor:\n" + JSON.stringify(data.errors));
                        return;
                    }

                    const selectProveedor = document.querySelector("#id_proveedor");
                    if (selectProveedor) {
                        const opt = new Option(data.nombre, data.id, true, true);
                        selectProveedor.appendChild(opt);
                    }

                    const modal = bootstrap.Modal.getInstance(modalProveedorEl);
                    modal?.hide();
                    formProveedor.reset();
                })
                .catch(err => {
                    console.error("Error AJAX proveedor:", err);
                    alert("Error inesperado al crear el proveedor.");
                });
        });
    }
});
