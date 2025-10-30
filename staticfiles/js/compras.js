// static/js/compras.js

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
}

function calcularSubtotal(row) {
    const insumoSelect = row.querySelector('.detalle-insumo');
    const cantidadInput = row.querySelector('.detalle-cantidad');
    const precioInput = row.querySelector('.detalle-precio');
    const subtotalInput = row.querySelector('.detalle-subtotal');

    const insumoId = insumoSelect?.value;
    let precio = parseFloat(precioInput.value) || 0;

    if (precio === 0 && insumoId && INSUMO_PRECIOS[insumoId]) {
        precio = parseFloat(INSUMO_PRECIOS[insumoId]);
        precioInput.value = precio.toFixed(2);
    }

    const cantidad = parseFloat(cantidadInput.value) || 0;
    subtotalInput.value = (precio * cantidad).toFixed(2);

    actualizarTotal();
}

function conectarEventosFila(row) {
    const insumo = row.querySelector(".detalle-insumo");
    const cantidad = row.querySelector(".detalle-cantidad");
    const precio = row.querySelector(".detalle-precio");

    if (insumo) insumo.addEventListener("change", () => calcularSubtotal(row));
    if (cantidad) cantidad.addEventListener("input", () => calcularSubtotal(row));
    if (precio) precio.addEventListener("input", () => calcularSubtotal(row));

    calcularSubtotal(row);
}

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".detalle-row").forEach(conectarEventosFila);
    actualizarTotal();

    // ➕ AGREGAR NUEVA LÍNEA
    const addRowButton = document.getElementById("add-row");
    const totalForms = document.querySelector("input[name='detallescompra_set-TOTAL_FORMS']");
    const tbody = document.getElementById("detalle-body");
    const template = document.getElementById("formset-empty");

    addRowButton.addEventListener("click", () => {
        let formIndex = Number(totalForms.value);
        let newRowHtml = template.innerHTML.replace(/__prefix__/g, formIndex);

        tbody.insertAdjacentHTML("beforeend", newRowHtml);

        const newRow = tbody.lastElementChild;
        conectarEventosFila(newRow);

        totalForms.value = formIndex + 1;
    });

    // ✅ AJAX PARA CREAR INSUMO DESDE MODAL
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

        document.querySelectorAll(".detalle-insumo").forEach(select => {
            const option = new Option(data.nombre, data.id, true, true);
            select.appendChild(option);
        });

        const lastRow = document.querySelector("#detalle-body").lastElementChild;
        if (lastRow) calcularSubtotal(lastRow);
    });


    const btnGuardarInsumo = document.getElementById("btnGuardarInsumo");
    if (btnGuardarInsumo) {
        btnGuardarInsumo.addEventListener("click", function () {
            document.getElementById("insumoFormModal").dispatchEvent(new Event("submit"));
        });
    }

});
