import React, { useState } from 'react';
import axios from 'axios';
import Map from './Map';
import './App.css';

const DEFAULT_SLIDER_VALUE = 0;

const parameterInfo = {
  'входы_выходы_станций_метро': {
    desc: 'Доступность метрополитена как основного вида быстрого транспорта.',
    radius: 500
  },
  'остановки_наземного_транспорта': {
    desc: 'Развитость автобусной, трамвайной и троллейбусной сети.',
    radius: 300
  },
  'станции_мцд': {
    desc: 'Доступ к пригородному железнодорожному сообщению.',
    radius: 1000
  },

  'больницы_взрослые': {
    desc: 'Наличие стационарной медицинской помощи.',
    radius: 2000
  },
  'поликлиническая_помощь_взрослым': {
    desc: 'Доступность амбулаторного лечения и консультаций.',
    radius: 800
  },
  'скорая_и_неотложная_медицинская_п': {
    desc: 'Оперативное реагирование в экстренных ситуациях.',
    radius: 3000
  },
  'специализированные_медицинские_у': {
    desc: 'Наличие профильных медицинских центров.',
    radius: 1500
  },
  'центры_вакцинации': {
    desc: 'Доступность профилактических медицинских услуг.',
    radius: 1500
  },

  'карта_школьных_зон': {
    desc: 'Закрепление территорий за образовательными учреждениями.',
    radius: 400
  },
  'образовательные_учреждения': {
    desc: 'Наличие школ, детских садов и других учебных заведений.',
    radius: 500
  },
  'образовательные_учреждения_город': {
    desc: 'Общая доступность образовательной инфраструктуры.',
    radius: 500
  },
  'организации_для_детей_сирот': {
    desc: 'Наличие специализированных социальных учреждений.',
    radius: 1000
  },

  'нестационарные_торговые_объекты': {
    desc: 'Киоски, павильоны и временные точки продаж.',
    radius: 300
  },
  'стационарные_торговые_объекты': {
    desc: 'Магазины, супермаркеты и торговые центры.',
    radius: 300
  },
  'общественное_питание': {
    desc: 'Кафе, рестораны и другие заведения питания.',
    radius: 300
  },

  'городской_wi_fi': {
    desc: 'Доступность бесплатного интернета в общественных местах.',
    radius: 200
  },
  'парковые_территории': {
    desc: 'Наличие зон отдыха и зеленых территорий.',
    radius: 700
  },
  'площадки_для_выгула_собак': {
    desc: 'Инфраструктура для владельцев домашних животных.',
    radius: 400
  },
  'стационарные_общественные_туалет': {
    desc: 'Уровень базового благоустройства городской среды.',
    radius: 400
  },

  'мфц': {
    desc: 'Доступность государственных и муниципальных услуг.',
    radius: 1000
  },
  'объекты_культурного_наследия': {
    desc: 'Наличие исторически и культурно значимых объектов.',
    radius: 500
  },
  'станции_контроля_загрязнения_атмо': {
    desc: 'Мониторинг экологической обстановки.',
    radius: 500
  }
};

const reliabilityOptions = [
  { id: 'any', label: 'Не учитывать' },
  { id: 'known', label: 'Есть оценка' },
  { id: 'medium', label: 'Средняя и выше' },
  { id: 'high', label: 'Высокая' },
];

function App() {
  // Группировка параметров по категориям
  const categories = [
    {
      name: "Транспортная инфраструктура",
      expanded: true,
      parameters: [
        // { id: 'автовокзалы_и_автостанции', label: 'Автовокзалы и автостанции' },
        { id: 'входы_выходы_станций_метро', label: 'Входы/выходы станций метро' },
        { id: 'остановки_наземного_транспорта', label: 'Остановки наземного транспорта' },
        { id: 'станции_мцд', label: 'Станции МЦД' },
        // { id: 'точки_продажи_билетов', label: 'Точки продажи билетов' },
      ]
    },
    {
      name: "Медицинские учреждения",
      expanded: true,
      parameters: [
        { id: 'больницы_взрослые', label: 'Больницы взрослые' },
        { id: 'поликлиническая_помощь_взрослым', label: 'Поликлиническая помощь взрослым' },
        { id: 'скорая_и_неотложная_медицинская_п', label: 'Скорая и неотложная мед. помощь' },
        { id: 'специализированные_медицинские_у', label: 'Специализированные мед. учреждения' },
        { id: 'центры_вакцинации', label: 'Центры вакцинации' },
        // { id: 'центры_тестирования_для_выбора_сп', label: 'Центры тестирования для выбора спорта' },
      ]
    },
    {
      name: "Образование и дети",
      expanded: true,
      parameters: [
        { id: 'карта_школьных_зон', label: 'Школьные зоны' },
        { id: 'образовательные_учреждения', label: 'Образовательные учреждения (культура)' },
        { id: 'образовательные_учреждения_город', label: 'Образовательные учреждения' },
        { id: 'организации_для_детей_сирот', label: 'Организации для детей-сирот' },
      ]
    },
    {
      name: "Торговля и питание",
      expanded: true,
      parameters: [
        { id: 'нестационарные_торговые_объекты', label: 'Нестационарные торговые объекты' },
        { id: 'стационарные_торговые_объекты', label: 'Стационарные торговые объекты' },
        { id: 'общественное_питание', label: 'Общественное питание' },
      ]
    },
    {
      name: "Городская среда",
      expanded: true,
      parameters: [
        { id: 'городской_wi_fi', label: 'Городской Wi-Fi' },
        { id: 'парковые_территории', label: 'Парковые территории' },
        { id: 'площадки_для_выгула_собак', label: 'Площадки для выгула собак' },
        { id: 'стационарные_общественные_туалет', label: 'Стационарные общественные туалеты' },
      ]
    },
    {
      name: "Госуслуги и культура",
      expanded: true,
      parameters: [
        { id: 'мфц', label: 'МФЦ' },
        { id: 'объекты_культурного_наследия', label: 'Объекты культурного наследия' },
        { id: 'станции_контроля_загрязнения_атмо', label: 'Станции контроля загрязнения атмосферы' },
      ]
    }
  ];

  // Функция для установки начальных значений
  const getInitialValues = () => {
    const initial = {};
    categories.forEach(category => {
      category.parameters.forEach(param => {
        initial[param.id] = DEFAULT_SLIDER_VALUE;
      });
    });
    return initial;
  };

  const [formValues, setFormValues] = useState(getInitialValues());
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reliabilityMode, setReliabilityMode] = useState('any');
  const [isWidgetVisible, setIsWidgetVisible] = useState(true);
  const [expandedCategories, setExpandedCategories] = useState(
    categories.reduce((acc, cat) => ({ ...acc, [cat.name]: cat.expanded }), {})
  );

  // Функция для сворачивания всех категорий
  const collapseAll = () => {
    const allCollapsed = {};
    categories.forEach(cat => {
      allCollapsed[cat.name] = false;
    });
    setExpandedCategories(allCollapsed);
  };

  // Функция для разворачивания всех категорий
  const expandAll = () => {
    const allExpanded = {};
    categories.forEach(cat => {
      allExpanded[cat.name] = true;
    });
    setExpandedCategories(allExpanded);
  };

  // Функция для обнуления всех категорий (сброс расширенных состояний)
  const resetAllCategories = () => {
    const resetValues = {};
    categories.forEach(category => {
      category.parameters.forEach(param => {
        resetValues[param.id] = DEFAULT_SLIDER_VALUE;
      });
    });
    setFormValues(resetValues);
  };

  const toggleCategory = (categoryName) => {
    setExpandedCategories({
      ...expandedCategories,
      [categoryName]: !expandedCategories[categoryName]
    });
  };

  const handleSliderChange = (id, value) => {
    setFormValues({
      ...formValues,
      [id]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {};
    categories.forEach(category => {
      category.parameters.forEach(param => {
        const value = formValues[param.id] !== undefined ? formValues[param.id] : DEFAULT_SLIDER_VALUE;
        if (value > 0) {
          payload[param.id] = value;
        }
      });
    });
    payload.reliability_mode = reliabilityMode;

    try {
      const response = await axios.post('http://localhost:8000/find', payload);
      // const response = await axios.post(' https://antenna-unlock-manufacturer-promises.trycloudflare.com/find', payload);
      console.log('Response:', response.data);
      const resultsArray = Object.values(response.data);
      setResults(resultsArray.slice(0, 5));
    } catch (err) {
      console.error('Error:', err);
      setError('Ошибка при получении данных. Убедитесь, что бэкенд запущен на порту 8000');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormValues(getInitialValues());
    setReliabilityMode('any');
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      <div className="map-container">
        <Map results={results} categories={categories} />

        {/* Кнопка показа виджета (когда он скрыт) */}
        {!isWidgetVisible && (
          <button
            className="show-widget-btn"
            onClick={() => setIsWidgetVisible(true)}
            title="Показать фильтры"
          >
            ⚙️
          </button>
        )}

        {/* Плавающий виджет */}
        {isWidgetVisible && (
          <div className="floating-widget">
            <div className="widget-header">
              <h3>Фильтры поиска</h3>
              <button
                className="hide-widget-btn"
                onClick={() => setIsWidgetVisible(false)}
                title="Скрыть фильтры"
              >
                ✕
              </button>
            </div>

            <div className="widget-controls">
              <button type="button" onClick={collapseAll} className="widget-icon-btn" title="Свернуть все">
                📁
              </button>
              <button type="button" onClick={expandAll} className="widget-icon-btn" title="Развернуть все">
                📂
              </button>
              <button type="button" onClick={resetAllCategories} className="widget-icon-btn" title="Обнулить все категории">
                🗑️
              </button>
              <button type="button" onClick={handleReset} className="widget-icon-btn" title="Сбросить значения">
                🔄
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="widget-parameters">
                <div className="reliability-filter">
                  <label>Надежность застройщика</label>
                  <div className="reliability-options">
                    {reliabilityOptions.map(option => (
                      <button
                        key={option.id}
                        type="button"
                        className={reliabilityMode === option.id ? 'reliability-option active' : 'reliability-option'}
                        onClick={() => setReliabilityMode(option.id)}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {categories.map(category => (
                  <div key={category.name} className="widget-category">
                    <div
                      className="widget-category-header"
                      onClick={() => toggleCategory(category.name)}
                    >
                      <span className="category-icon">
                        {expandedCategories[category.name] ? '▼' : '▶'}
                      </span>
                      <span className="category-name">{category.name}</span>
                      <span className="category-count">
                        {category.parameters.length}
                      </span>
                    </div>

                    {expandedCategories[category.name] && (
                      <div className="widget-category-parameters">
                        {category.parameters.map(param => (
                          <div key={param.id} className="widget-parameter">
                            <div className="tooltip-container">
                              <label>{param.label}</label>
                              {parameterInfo[param.id] && (
                                <div className="tooltip-box">
                                  <div>{parameterInfo[param.id].desc}</div>
                                  <div className="tooltip-radius">
                                    Радиус влияния: {parameterInfo[param.id].radius} м
                                    <br />
                                    <span className="tooltip-note">
                                      Значимость объекта уменьшается с расстоянием.
                                    </span>
                                  </div>
                                                                  </div>
                              )}
                            </div>
                            <div className="widget-slider-container">
                              <input
                                type="range"
                                min="0"
                                max="10"
                                step="1"
                                value={formValues[param.id] !== undefined ? formValues[param.id] : DEFAULT_SLIDER_VALUE}
                                onChange={(e) => handleSliderChange(param.id, parseInt(e.target.value))}
                              />
                              <span className="widget-value">
                                {formValues[param.id] !== undefined ? formValues[param.id] : DEFAULT_SLIDER_VALUE}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <button type="submit" disabled={loading} className="widget-search-btn">
                {loading ? 'Поиск...' : 'Найти'}
              </button>

              {error && <div className="widget-error">{error}</div>}

              {results && (
                <div className="widget-results-info">
                  Найдено: {results.length}
                </div>
              )}
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
