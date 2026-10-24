import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Фикс для иконок Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Компонент для центрирования карты
function MapCenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 12);
    }
  }, [center, map]);
  return null;
}

function Map({ results, categories }) {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [center, setCenter] = useState([55.751244, 37.618423]);
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [dossier, setDossier] = useState(null);
  const [dossierLoading, setDossierLoading] = useState(false);
  const [dossierError, setDossierError] = useState(null);

  // Функция для получения координат
  const getCoordinates = (location) => {
    const lat = location.latitude || location.lat || location.y;
    const lng = location.longitude || location.lon || location.x;
    return { lat, lng };
  };

  // Функция для получения полей из categories
  const getLocationFields = (location) => {
    const fields = [];

    for (const category of categories) {
      for (const param of category.parameters) {
        if (location[param.id] !== undefined && location[param.id] !== null) {
          fields.push({
            key: param.id,
            label: param.label,
            value: location[param.id]
          });
        }
      }
    }

    return fields;
  };

  const handleMarkerClick = (location) => {
    setSelectedLocation(location);
    setIsDossierOpen(false);
    setDossier(null);
    setDossierError(null);
  };

  const openLocationDetails = (location) => {
    const { lat, lng } = getCoordinates(location);
    if (lat && lng) {
      setCenter([lat, lng]);
    }
    handleMarkerClick(location);
  };

  const closeDetails = () => {
    setSelectedLocation(null);
    setIsDossierOpen(false);
    setDossier(null);
    setDossierError(null);
  };

  const formatScore = (score) => {
    if (score === undefined || score === null || score === '') {
      return 'нет оценки';
    }
    return `${Math.round(Number(score))}/100`;
  };

  const formatPercent = (value) => {
    if (value === undefined || value === null) {
      return 'нет данных';
    }
    return `${Math.round(Number(value) * 100)}%`;
  };

  const formatNumber = (value) => {
    if (value === undefined || value === null) {
      return 'нет данных';
    }
    return Number.isInteger(value) ? value : Number(value).toFixed(1);
  };

  const criteriaLabels = {
    deadline_discipline: 'Соблюдение сроков',
    problem_objects: 'Проблемные объекты',
    legal_risk: 'Правовые риски',
    reputation_risk: 'Репутация'
  };

  const factorLabels = {
    registration_date: 'Дата регистрации',
    projects_count: 'Проектов',
    problem_projects_count: 'Проблемных проектов',
    delayed_projects_count: 'Проектов с задержками',
    avg_delay_days: 'Средняя задержка, дней',
    legal_events_count: 'Правовых событий',
    news_mentions: 'Новостных упоминаний',
    scored_news_count: 'Оценённых новостей',
    neutral_news_count: 'Нейтральных новостей',
    negative_news_share: 'Доля негатива в новостях'
  };

  const loadDossier = async () => {
    if (!selectedLocation?.developer_inn) {
      return;
    }

    if (dossier) {
      setIsDossierOpen(!isDossierOpen);
      return;
    }

    setIsDossierOpen(true);
    setDossierLoading(true);
    setDossierError(null);

    try {
      const response = await axios.get(
        `http://localhost:8000/ratings/developers/${selectedLocation.developer_inn}/dossier`
      );
      setDossier(response.data);
    } catch (error) {
      console.error('Dossier loading error:', error);
      setDossierError('Не удалось загрузить подробности оценки');
    } finally {
      setDossierLoading(false);
    }
  };

  const renderDossier = () => {
    if (!isDossierOpen) {
      return null;
    }

    if (dossierLoading) {
      return <div className="rating-dossier-state">Загружаем данные оценки...</div>;
    }

    if (dossierError) {
      return <div className="rating-dossier-state error">{dossierError}</div>;
    }

    if (!dossier) {
      return null;
    }

    const criteria = dossier.details?.criteria || {};
    const weights = dossier.details?.weights || {};
    const factors = dossier.factors || {};
    const warnings = dossier.details?.data_warnings || [];
    const unknownReasons = dossier.details?.unknown_reasons || [];

    return (
      <div className="rating-dossier">
        <div className="rating-dossier-summary">
          <span>{dossier.status || 'Статус не определён'}</span>
          <strong>{formatScore(dossier.score)}</strong>
        </div>

        {(warnings.length > 0 || unknownReasons.length > 0) && (
          <div className="rating-notes">
            {[...unknownReasons, ...warnings].map((item, index) => (
              <div key={index}>{item}</div>
            ))}
          </div>
        )}

        <h4>Критерии оценки</h4>
        <div className="criteria-list">
          {Object.entries(criteria).map(([key, value]) => (
            <div className="criteria-row" key={key}>
              <span>{criteriaLabels[key] || key}</span>
              <strong>{value === null ? 'нет данных' : formatPercent(value)}</strong>
              <small>вес {formatPercent(weights[key])}</small>
            </div>
          ))}
        </div>

        <h4>Исходные данные</h4>
        <div className="factor-grid">
          {Object.entries(factorLabels).map(([key, label]) => {
            const value = factors[key];
            const formatted = key.includes('share')
              ? formatPercent(value)
              : key.includes('date')
                ? (value || 'нет данных')
                : formatNumber(value);
            return (
              <div className="factor-item" key={key}>
                <span>{label}</span>
                <strong>{formatted}</strong>
              </div>
            );
          })}
        </div>

        {dossier.projects?.length > 0 && (
          <>
            <h4>Проекты застройщика</h4>
            <div className="dossier-list">
              {dossier.projects.slice(0, 5).map((project, index) => (
                <div className="dossier-list-item" key={`${project.name}-${index}`}>
                  <strong>{project.name || 'Проект без названия'}</strong>
                  <span>
                    Задержка: {formatNumber(project.delay_days_avg)} дн.
                    {project.is_problem ? ' · проблемный объект' : ''}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {dossier.legal_events?.length > 0 && (
          <>
            <h4>Правовые события</h4>
            <div className="dossier-list">
              {dossier.legal_events.slice(0, 3).map((event, index) => (
                <div className="dossier-list-item" key={`${event.date}-${index}`}>
                  <strong>{event.event_type || 'Событие'}</strong>
                  <span>{event.date} · {event.status || 'статус не указан'}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {dossier.news?.length > 0 && (
          <>
            <h4>Новости и репутация</h4>
            <div className="dossier-list">
              {dossier.news.slice(0, 5).map((news, index) => (
                <a
                  className="dossier-list-item link"
                  href={news.link}
                  target="_blank"
                  rel="noreferrer"
                  key={`${news.title}-${index}`}
                >
                  <strong>{news.title || 'Новость без заголовка'}</strong>
                  <span>{news.published_at || 'дата не указана'} · {news.sentiment || 'тональность не определена'}</span>
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  const getReliabilityStatus = (location) => {
    const score = location?.developer_reliability_score;
    if (score === undefined || score === null || score === '') {
      return 'Надёжность не рассчитана';
    }

    const numericScore = Number(score);
    if (numericScore >= 80) {
      return 'Высокая надёжность';
    }
    if (numericScore >= 60) {
      return 'Средняя надёжность';
    }
    if (numericScore >= 40) {
      return 'Рискованный';
    }
    return 'Высокий риск';
  };

  const getReliabilityClass = (location) => {
    const score = location?.developer_reliability_score;
    if (score === undefined || score === null || score === '') {
      return 'unknown';
    }

    const numericScore = Number(score);
    if (numericScore >= 80) {
      return 'high';
    }
    if (numericScore >= 60) {
      return 'medium';
    }
    if (numericScore >= 40) {
      return 'risky';
    }
    return 'low';
  };

  useEffect(() => {
    if (results && results.length > 0) {
      const firstPoint = results[0];
      const { lat, lng } = getCoordinates(firstPoint);
      if (lat && lng) {
        setCenter([lat, lng]);
      }
    }
  }, [results]);

  if (!results || results.length === 0) {
    return (
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
      >
        <MapCenter center={center} />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
      </MapContainer>
    );
  }

  return (
    <>
      <div className="map-results-layout">
        <aside className="results-panel">
          <div className="results-panel-header">
            <span>Подобранные новостройки</span>
            <strong>{results.length}</strong>
          </div>
          <div className="results-list">
            {results.map((location, index) => (
              <button
                className="result-card"
                key={`${location.id || location.address}-${index}`}
                onClick={() => openLocationDetails(location)}
              >
                <span className="result-index">{index + 1}</span>
                <span className="result-body">
                  <strong>{location.address || 'Адрес не указан'}</strong>
                  <span>{location.developer_name || 'Застройщик не указан'}</span>
                  <span className={`result-reliability ${getReliabilityClass(location)}`}>
                    {formatScore(location.developer_reliability_score)} · {getReliabilityStatus(location)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </aside>

        <div className="map-view">
          <MapContainer
            center={center}
            zoom={12}
            style={{ height: '100%', width: '100%' }}
          >
            <MapCenter center={center} />
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            {results.map((location, index) => {
              const { lat, lng } = getCoordinates(location);

              if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
                console.warn('Invalid coordinates for location:', location);
                return null;
              }

              return (
                <Marker
                  key={index}
                  position={[lat, lng]}
                  eventHandlers={{
                    click: () => openLocationDetails(location)
                  }}
                >
                  {/* <Popup>
                    <div>
                      <strong>{location.address || 'Объект'}</strong>
                    </div>
                  </Popup> */}
                </Marker>
              );
            })}
          </MapContainer>
        </div>
      </div>

      {selectedLocation && (
        <div className="details-panel" onClick={closeDetails}>
          <div className="details-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={closeDetails}>×</button>
            <h3>📍 {selectedLocation.address || 'Адрес не указан'}</h3>
            {selectedLocation.developer_name && (
              <div className="developer-card">
                <div>
                  <span className="developer-label">Застройщик</span>
                  <button
                    className="developer-name"
                    onClick={loadDossier}
                    disabled={!selectedLocation.developer_inn}
                  >
                    {selectedLocation.developer_name}
                  </button>
                  {selectedLocation.developer_inn && (
                    <span className="developer-inn">ИНН {selectedLocation.developer_inn}</span>
                  )}
                </div>
                <div className="developer-score">
                  <strong>{formatScore(selectedLocation.developer_reliability_score)}</strong>
                  <span>{getReliabilityStatus(selectedLocation)}</span>
                </div>
                {selectedLocation.developer_inn && (
                  <button className="dossier-toggle" onClick={loadDossier}>
                    {isDossierOpen ? 'Свернуть' : 'Развернуть оценку'}
                  </button>
                )}
              </div>
            )}
            {renderDossier()}
            <div className="details-grid">
              {getLocationFields(selectedLocation).map(({ key, label, value }) => (
                <div key={key} className="detail-item">
                  <span className="detail-label">{label}:</span>
                  <span className="detail-value">{Math.round(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Map;
