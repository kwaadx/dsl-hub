package dsl

type Root struct {
	Version   string      `json:"version"`
	Meta      interface{} `json:"meta"`
	Policies  interface{} `json:"policies"`
	Obs       interface{} `json:"observability"`
	Conns     interface{} `json:"connections"`
	Sources   interface{} `json:"sources"`
	Actions   interface{} `json:"actions"`
	Pipelines []Pipeline  `json:"pipelines"`
	Testing   interface{} `json:"testing"`
}

type Pipeline struct {
	ID       string    `json:"id"`
	Enabled  *bool     `json:"enabled,omitempty"`
	Triggers []Trigger `json:"triggers"`
}

type Trigger struct {
	Type      string    `json:"type"`
	Every     string    `json:"every,omitempty"`
	Cron      string    `json:"cron,omitempty"`
	Window    *struct{} `json:"window,omitempty"`
	Event     string    `json:"event,omitempty"`
	Intent    string    `json:"intent,omitempty"`
	Threshold int       `json:"threshold,omitempty"`
}
