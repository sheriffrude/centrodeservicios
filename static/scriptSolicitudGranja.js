/* INICIO OBTENER INFORMACION DE SOLICITUD A GRANJAS */
window.onload = GuardarLocalStorage();

function GuardarLocalStorage(){
	var data = [];
    var dataInLocalStorage = localStorage.getItem("producto");
    var tbody = document.getElementById('TablaSolicitudGranja');

	if(dataInLocalStorage !== null){
        data = JSON.parse(dataInLocalStorage);
    }

	tbody.innerHTML = '';

	data.forEach(function(x, i){
		var plantilla = `
			<tr class="selected">
				<td id="cerdo${i}" class="tdd">CERDO</td>
				<td class="tdd">
					<input type="number" min="0" name="cantidadCerdos${i}" id="cantidadCerdos${i}" value="${x.cantidadCerdos}" class="form form-control" >
				</td>
				<td class="tdd">
					<input style="width: 130px;" type="text" name="observacion${i}" id="observacion${i}" value="${x.observacion}" class="form form-control">
				</td>
				<td class="tdd">
					<select style="width: 130px;" class="custom-select" name="selectFrigorifico${i}" id="selectFrigorifico${i}">
						<option selected="selected" value="${x.selectFrigorifico}">${x.selectFrigorifico}</option>
						<option value="Frigotun">Frigotun</option>
						<option value="Frigocentro">Frigocentros</option>
						<option value="Oinc">Oinc</option>
						<option value="Frigotimana">Frigotimana</option>
						<option value="Frigoprogresar">Frigoprogresar</option>
					</select>
				</td>
				<br>
				<td class="tdd">
					<input type="date" name="fechaDisponibilidad${i}" id="fechaDisponibilidad${i}" value="${x.fechaDisponibilidad}" style="width: 170px;" class="form form-control">
				</td>
				<td class="tdd" style="padding-left: 5%;">
					<div class="row">
						<button type="button" name="SolicitudEliminarCanal" value='${i}' data-toggle="modal" data-target="#SolicitudEliminarCanal" class="col-sm-8 btn btn-danger" data-toggle="tooltip" data-placement="top" title="Eliminar solicitud" onclick="eliminarProducto(this)"><img src="http://intranet.cercafe.com/comercialCopiaNueva/public/svg/delete.png" alt="icono-Eliminar" style="width: 11px; height: 11px;"></button>
					</div>
				</td>
			</tr>
		`;
		tbody.innerHTML += plantilla;
	});
}

var botonAgregarFila = document.getElementById('bt_add'); 

botonAgregarFila.addEventListener('click', ValidarData);

function ValidarData() {
	var array = [];
	var bodyTable = document.getElementById('TablaSolicitudGranja');

	for (let i = 0; i < bodyTable.rows.length; i++){
		var cerdo = document.getElementById('cerdo'+i);
        var cantidadCerdos = document.getElementById('cantidadCerdos'+i);
        var observacion = document.getElementById('observacion'+i);
        var selectFrigorifico = document.getElementById("selectFrigorifico"+i);
        var fechaDisponibilidad = document.getElementById("fechaDisponibilidad"+i);

		var ObtProductos = {
            cerdo: cerdo.innerHTML,
            cantidadCerdos: cantidadCerdos.value,
            observacion: observacion.value,
            selectFrigorifico: selectFrigorifico.value,
			fechaDisponibilidad: fechaDisponibilidad.value,
        }
		array.push(ObtProductos);
	}

	var ObtProductos = {
        cerdo: 'CERDO',
        cantidadCerdos: 0,
        observacion: '',
		selectFrigorifico: '',
        fechaDisponibilidad: '0000-00-00'
    }

    array.push(ObtProductos);

    localStorage.setItem("producto", JSON.stringify(array));
    GuardarLocalStorage();
}

/* FIN OBTENER INFORMACION DE SOLICITUD A GRANJAS */

/* INICIO ELIMINAR INFORMACION DE SOLICITUD A GRANJAS */
function eliminarProducto(boton){
    localStorage.setItem("borrar", boton.value);
}

document.getElementById('cerrarModalEliminar').addEventListener('click', function(){
    localStorage.removeItem("borrar");
})

document.getElementById('BotonEliminarModal').addEventListener('click', function(){
	var array = [];
	var bodyTableAEliminar = document.getElementById('TablaSolicitudGranja');

	for (let i = 0; i < bodyTableAEliminar.rows.length; i++){
		var cerdo = document.getElementById('cerdo'+i);
        var cantidadCerdos = document.getElementById('cantidadCerdos'+i);
        var observacion = document.getElementById('observacion'+i);
        var selectFrigorifico = document.getElementById("selectFrigorifico"+i);
        var fechaDisponibilidad = document.getElementById("fechaDisponibilidad"+i);

		var ObtProductosEliminacion = {
			cerdo: cerdo.innerHTML,
            cantidadCerdos: cantidadCerdos.value,
            observacion: observacion.value,
            selectFrigorifico: selectFrigorifico.value,
			fechaDisponibilidad: fechaDisponibilidad.value,
        }
		array.push(ObtProductosEliminacion);
	}

	localStorage.setItem("producto", JSON.stringify(array));

    var posicion = localStorage.getItem("borrar");

    var contenidoTable = [];
        contenidoTable = JSON.parse(localStorage.getItem("producto"));
        contenidoTable.splice(posicion, 1);
        localStorage.setItem("producto", JSON.stringify(contenidoTable));
    
    document.getElementById('cerrarModalEliminar').click();

    GuardarLocalStorage();

});
/* FIN ELIMINAR INFORMACION DE SOLICITUD A GRANJAS */ 





/* INICIO OBTENER INFORMACION DE MODULO EDICION */
function GuardarEdicionLocalStorage(){
	var data = [];
    var dataInLocalStorage = localStorage.getItem("productoaEditar");
    var tbodyEdicion = document.getElementById('TablaEdit');

	if(dataInLocalStorage !== null){
        data = JSON.parse(dataInLocalStorage);
    }
	console.log('Datos Parseados');
	console.log(data);
	tbodyEdicion.innerHTML = '';

	data.forEach(function(element, i){
		var plantillaEdicion = `
		<tr class="selected" id="filaEdicion'+i+'">
			<input type="hidden" id="idSolicitud${i}" value="${element.idSolicitud}">
			<td id="producto${i}">CERDO</td>
			<td>
				<input type="number" id="cantidad${i}" class="form form-control" value="${element.cantidad}">
			</td>
			<td>
				<input type="text" id="observacion${i}" class="form form-control" value="${element.observacion}">
			</td>
			<td>
				<input type="text" id="frigorificoEdicion${i}" class="form form-control" value="${element.frigorificoEdicion}">
			</td>
			<td>
				<input type="date" id="fecha${i}" class="form form-control" value="${element.fecha}">
			</td>
			<td style="padding-left: 3.5%;">
				<div class="row">
					<button type="button" id="EliminarModuloEdicion${i}" value="${i}" onclick="eliminarProductoEditado(this)" name="EliminarModuloEdicion" class="btn btn-danger" data-toggle="tooltip" data-placement="top" title="Eliminar solicitud" onclick=""><img src="http://intranet.cercafe.com/comercialCopiaNueva/public/svg/delete.png" alt="icono-Eliminar" style="width: 11px; height: 11px;"></button>
				</div>
			</td>
		</tr>
		`;
		tbodyEdicion.innerHTML += plantillaEdicion;
	});
}

function ValidarDataEdicion(){
	var array = [];
	var bodyTableEdicion = document.getElementById('TablaEdit');

	for (let i = 0; i < bodyTableEdicion.rows.length; i++){
		var idSolicitud = document.getElementById('idSolicitud'+i);
        var producto = document.getElementById('producto'+i);
        var cantidad = document.getElementById('cantidad'+i);
        var observacion = document.getElementById('observacion'+i);
		var frigorificoEdicion = document.getElementById('frigorificoEdicion'+i);
        var fecha = document.getElementById("fecha"+i);

		var ObtProductosEdicion = {
			idSolicitud: idSolicitud.value,
            producto: producto.innerHTML,
            cantidad: cantidad.value,
            observacion: observacion.value,
			frigorificoEdicion: frigorificoEdicion.value,
			fecha: fecha.value,
        }

		array.push(ObtProductosEdicion);
	}

    localStorage.setItem("productoaEditar", JSON.stringify(array));
    GuardarEdicionLocalStorage();
}

function eliminarProductoEditado(valor){
    var boton = valor.value;

    var contenidoTable = [];
        contenidoTable = JSON.parse(localStorage.getItem("productoaEditar"));
        contenidoTable.splice(boton, 1);
        localStorage.setItem("productoaEditar", JSON.stringify(contenidoTable));

    GuardarEdicionLocalStorage();

};
/* FIN OBTENER INFORMACION DE MODULO EDICION */




document.getElementById('solicitarPedido').addEventListener('click', function(){
	if(validacion()){
		/* console.log('entro'); */
		var datos = saveData();
		/* console.log(datos); */
		sendData(datos);
	}
})

function validacion(){
	var tabla = document.getElementById('tablaSolicitudCerdosGranja');
	var filas = tabla.rows.length - 1;
	var granja = document.getElementById('selectGranja').value;
	/* console.log(filas); */
	if(granja == 0 || granja == ''){
		alert('Debe seleccionar una granja para continuar');
			return false;
	}
	for(let i = 0; i < filas; i++){
		var cantidad = document.getElementById('cantidadCerdos'+i).value;
		var frigorifico = document.getElementById('selectFrigorifico'+i).value;
		var fecha = document.getElementById('fechaDisponibilidad'+i).value;
		if(cantidad == '' || cantidad == 0){
			alert('Debe ingresar un dato valido en la cantidad de la fila numero '+(i + 1));
			return false;
		}
		else if(frigorifico == 0){
			alert('Debe seleccionar un frigorifico en la fila numero '+(i + 1));
			return false;
		}
		else if(fecha.length == 0){
			alert('Debe seleccionar una fecha en la fila numero '+(i + 1));
			return false;
		}
		
	}
	return true;
}

function saveData(){
	var tabla = document.getElementById('tablaSolicitudCerdosGranja');
	var filas = tabla.rows.length - 1;
	
	var array = [];
	for(let i = 0; i<filas; i++){
		var cantidad = document.getElementById('cantidadCerdos'+i).value;
		var frigorifico = document.getElementById('selectFrigorifico'+i).value;
		let idIntranet = document.getElementById('idDispoIntranet'+i).value;
		var fecha = document.getElementById('fechaDisponibilidad'+i).value;
		var observacion = document.getElementById('observacion'+i).value;
		var datos = {
			cantidad: cantidad,
			frigorifico: frigorifico,
			fecha:fecha,
			observacion:observacion,
			idIntranet: idIntranet
		}
		array.push(datos);
	}
	return array;
}

function sendData(datos){
	var correo = localStorage.getItem('email');
	var inputCorreo = document.createElement('input');
		inputCorreo.type = 'hidden';
		inputCorreo.name = 'correo';
		inputCorreo.value = correo;

	var form = document.getElementById('formDisponibilidad');
	var inputDisponibilidad = document.createElement('input');
		inputDisponibilidad.name = 'disponibilidad';
		inputDisponibilidad.type = 'hidden';
		inputDisponibilidad.value = JSON.stringify(datos);

	var fecha = new Date();
	var fechaSolicitud = fecha.getFullYear()+"-"+
                            (fecha.getMonth() + 1)+"-"+
                            fecha.getDate()+" "+
                            fecha.getHours()+":"+
                            fecha.getMinutes()+":"+
                            fecha.getSeconds();

							
	var inputfechaSolicitud = document.createElement("input");
		inputfechaSolicitud.type = "hidden";
		inputfechaSolicitud.name = "fechaSolicitud";
		inputfechaSolicitud.value = fechaSolicitud;

	var granja = document.getElementById('selectGranja').value;
	var inputGranja = document.createElement('input');
		inputGranja.type = 'hidden';
		inputGranja.name = 'granja';
		inputGranja.value = granja;

	let fechaIni = document.getElementById('fechaIni').value;
	let inputFechaIni = document.createElement('input');
		inputFechaIni.type = 'hidden';
		inputFechaIni.name = 'fechaIni';
		inputFechaIni.value = fechaIni;


	let fechaFin = document.getElementById('fechaFin').value;
	let inputFechaFin = document.createElement('input');
		inputFechaFin.type = 'hidden';
		inputFechaFin.name = 'fechaFin';
		inputFechaFin.value = fechaFin;

	form.appendChild(inputDisponibilidad);
	form.appendChild(inputfechaSolicitud);
	form.appendChild(inputGranja);
	form.appendChild(inputCorreo);
	form.appendChild(inputFechaIni);
	form.appendChild(inputFechaFin);

	
	localStorage.removeItem('producto');

	form.submit();
}


document.getElementById('editarPedido').addEventListener('click',function(){
	let tabla = document.getElementById('tablaEdicion');
	let filas = tabla.rows.length - 1;
	
	if(filas != 0){
		let array = [];
		for(let i = 0; i<filas; i++){
			let idSolicitud = document.getElementById('idSolicitud'+i).value;
			let producto = document.getElementById('producto'+i).innerHTML;
			let cantidad = document.getElementById('cantidad'+i).value;
			let observacion = document.getElementById('observacion'+i).value;
			let frigorifico = document.getElementById('frigorificoEdicion'+i).value;
			let fecha = document.getElementById('fecha'+i).value;

			var datos = {
				idSolicitud: idSolicitud,
				producto: producto,
				cantidad: cantidad,
				observacion: observacion,
				frigorifico: frigorifico,
				fecha: fecha
			}

			array.push(datos);
		}
		
		let form = document.getElementById('formEdicion');
		let inputDatos = document.createElement('input');
			inputDatos.name = 'datosEdicion';
			inputDatos.type = 'hidden';
			inputDatos.value = JSON.stringify(array);
		
		form.appendChild(inputDatos);
		localStorage.removeItem('productoaEditar');
		form.submit();

	}
	else{
		alert('El pedido no puede quedar vacio');
	}
	console.log(filas);
})

