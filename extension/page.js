//externalAPI.on(externalAPI.EVENT_READY, function() {

//console.log("Injected>Ready");
addEventListener('message', function(ev) {
	if (ev.source != window) return;
	if (ev.data.YaMusic != 'Server2Extension') {
		return;
	} else {
		delete ev.data.YaMusic;
	}
	//console.log("Injected>Message: " + data);
	for (let key of Object.keys(ev.data)) {
		let val = ev.data[key];
		if (val === null) {
			val = undefined;
		}
		externalAPI[key](val);
	}
});

function registerEvent(name, apiName, get_info) {
	//console.log("Injected>Register: " + name);
	externalAPI.on(apiName, function(ev) {
		//console.log("Injected>" + name + ": " + ev);
		if (name == 'advert') {
			console.log(ev);
		}
		let info = get_info
			? get_info(ev)
			: undefined;
		window.postMessage({
			"event": name,
			"body": info,
			"YaMusic": "Extension2Server"
		});
	});
}

function playerState() {
	return {
		'isPlaying': externalAPI.isPlaying(),
		'shuffle': externalAPI.getShuffle(),
		'repeat': externalAPI.getRepeat(),
		'volume': externalAPI.getVolume(),
		'speed': externalAPI.getSpeed(),
		'progress': externalAPI.getProgress(),
	}
}

function trackState() {
	return {
		'current': externalAPI.getCurrentTrack(),
		'next': externalAPI.getNextTrack(),
		'prev': externalAPI.getPrevTrack(),
		'index': externalAPI.getTrackIndex(),
	}
}

registerEvent("ready", externalAPI.EVENT_READY);
registerEvent("advert", externalAPI.EVENT_ADVERT, (ev) => ev);
registerEvent("state", externalAPI.EVENT_STATE, (_) => playerState());
registerEvent("track", externalAPI.EVENT_TRACK, (_) => trackState());
registerEvent("controls", externalAPI.EVENT_CONTROLS, (_) => externalAPI.getControls());
registerEvent("source", externalAPI.EVENT_SOURCE_INFO, (_) => externalAPI.getSourceInfo());
registerEvent("list", externalAPI.EVENT_TRACKS_LIST, (_) => externalAPI.getTracksList());
registerEvent("volume", externalAPI.EVENT_VOLUME, (_) => externalAPI.getVolume() || -1);
registerEvent("speed", externalAPI.EVENT_SPEED, (_) => externalAPI.getSpeed());
registerEvent("progress", externalAPI.EVENT_PROGRESS, (_) => externalAPI.getProgress());

function send_state() {
	let state = {
		'controls': externalAPI.getControls(),
		'source': externalAPI.getSourceInfo(),
		'list': externalAPI.getTracksList(),

		'track': trackState(),
		'player': playerState(),
	};
	window.postMessage({
		"event": "full_state",
		"body": state,
		"YaMusic": "Extension2Server"
	});
	setTimeout(send_state, 1000);
}
send_state();

// }); //externalAPI.on(externalAPI.EVENT_READY, function() {

/*
Внешний интерфейс для расширений Яндекс.Музыки и Яндекс.Радио. Быстрая справка.
===============================================================================

Используемые форматы данных
---------------------------

Формат описания обложки:
  Ссылка на обложку. Либо строка либо набор строк для составных обложек.
  В ссылке присутствует подстрока "%%", которую требуется заменить на необходимое разрешение.'),
  Доступны разрешения 30x30, 50x50, 80x80, 100x100, 200x200, 300x300, 400x400

Формат описания трека:
  {String} title - название трека
  {String} link - ссылка на трек
  {Number} duration - длительность трека в секундах
  {Boolean} liked - трек залайкан
  {Boolean} disliked - трек задислайкан
  {Array.<ExternalAPI~ArtistInfo>} artists - список исполнителей
  {String} [version] - версия трека
  {ExternalAPI~AlbumInfo} [album] - альбом трека
  {ExternalAPI~CoverInfo} [cover] - обложка

Формат описания альбома:
  {String} title - название альбома
  {Number} year - год выпуска
  {String} link - ссылка на альбом
  {Array.<ExternalAPI~ArtistInfo>} artists - список исполнителей
  {ExternalAPI~CoverInfo} [cover] - обложка

Формат описания исполнителя:
  {String} title - имя исполнителя
  {String} link - ссылка на исполнителя
  {ExternalAPI~CoverInfo} [cover] - обложка

Формат описания плейлиста:
  {String} title - название плейлиста
  {String} owner - имя владельца плейлиста
  {String} link - ссылка на плейлист
  {ExternalAPI~CoverInfo} [cover] - обложка

Формат описания элементов управления:
  index - возможность запускать воспроизведние трека по его индексу
  next - возможность переключения на следующий трек
  prev - возможность переключение на предудущий трек
  shuffle - возможность включать шаффл
  repeat - возможность включать режим повтора треков
  like - возможность добавлять трек в избранное
  dislike - возможность добавлять трек в чёрный список
Все поля могут принимать изначения из списка констант:
  CONTROL_ENABLED - доступно
  CONTROL_DISABLED - недоступно
  CONTROL_DENIED - функция отсутствует

Формат описания временных метрик трека (все значения указываются в секундах):
  {Number} position - позиция воспроизведения
  {Number} duration - длительность трека
  {Number} loaded - длительность загруженной части


Программный интерфейс
---------------------

Получение данных о треках и текущем источнике:
  getCurrentTrack - данные о текущем треке
  getNextTrack - данные о следующем треке
  getPrevTrack - данные о предыдущем треке
  getTracksList - данные о списке треков
  getTrackIndex - индекс текущего трека в списке треков
  getSourceInfo - данные о текущем источнике воспроизведения
  populate(fromIndex, [after], [before], [ordered]) - подгрузка данных о треках в текущий список воспроизведения. В случае выставления флага ordered, треки будут загружаться с учётом порядка воспроизведения, а не положения в списке

Получение состояния плеера:
  isPlaying - проверка, что плеер запущен и не на паузе
  getControls - получение данных о доступности элементов управления
  getShuffle - получение состояния шаффла (SHUFFLE_ON/SHUFFLE_OFF)
  getRepeat - получение состояния повтора треков (REPEAT_NONE/REPEAT_ALL/REPEAT_ONE)
  getVolume - получние текущей громкости
  getSpeed - получние текущей скорости
  getProgress - получение данных о временных метриках трека

Управление плеером:
  play([index]) - запуск воспроизведения трека с указанным индексом. Если индекс не указан, будет запущен текущий выбранный трек
  next - переключение на следующий трек
  prev - переключение на предыдущий трек
  togglePause([state]) - поставить трек на паузу/снять паузу
  toggleLike - добавить трек в избранное/удалить трек из избранного
  toggleDislike - добавить трек в чёрный список/удалить трек из чёрного списка
  toggleShuffle([state]) - переключить режим шаффла (SHUFFLE_ON/SHUFFLE_OFF)
  toggleRepeat([state]) - переключить режим повтора треков (REPEAT_NONE/REPEAT_ALL/REPEAT_ONE)
  setVolume(value) - установить громкость
  setSpeed(value) - установить скорость
  toggleMute(state) - включит/выключить звук
  setPosition(value) - установить позицию воспроизведения

Дополнительные команды:
  navigate(url) - переход на страницу с указанным адресом. Адрес задаётся без протокола и домена

События
-------

Все события являются "чистыми" - в обработчик не передаётся никаких данных. Исключением является событие EVENT_ADVERT - в него передаются данные о рекламе, если она началась или false - если закончилась'),

EVENT_READY - готовность данного интерфейса
EVENT_STATE - изменение состояния плеера
EVENT_TRACK - смена трека
EVENT_ADVERT - воспроизведение рекламы
EVENT_CONTROLS - изменение состояния элементов управления (в т.ч. смены состояния шаффла и повтора треков)
EVENT_SOURCE_INFO - смена источника воспроизведения
EVENT_TRACKS_LIST - изменения списка треков
EVENT_VOLUME - изменение громкости
EVENT_SPEED - изменение скорости
EVENT_PROGRESS - изменение временных метрик трека
*/
