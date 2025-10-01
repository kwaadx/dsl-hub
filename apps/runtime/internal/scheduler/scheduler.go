package scheduler

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/robfig/cron/v3"

	"github.com/your-org/dsl-hub-runtime/internal/dsl"
)

type Runtime struct {
	Inbox        string
	Outbox       string
	PollInterval time.Duration
	loaded       map[string]bool
}

func New(inbox, outbox string, poll time.Duration) *Runtime {
	return &Runtime{
		Inbox:        inbox,
		Outbox:       outbox,
		PollInterval: poll,
		loaded:       make(map[string]bool),
	}
}

func (r *Runtime) Run() error {
	_ = os.MkdirAll(r.Inbox, 0o755)
	_ = os.MkdirAll(r.Outbox, 0o755)

	fmt.Printf("[runtime] up: inbox=%s outbox=%s interval=%s\n", r.Inbox, r.Outbox, r.PollInterval)

	for {
		_ = r.scanOnce()
		time.Sleep(r.PollInterval)
	}
}

func (r *Runtime) scanOnce() error {
	return filepath.WalkDir(r.Inbox, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d == nil {
			return nil
		}
		if d.IsDir() {
			return nil
		}
		name := strings.ToLower(d.Name())
		if !strings.HasSuffix(name, ".dsl.json") {
			return nil
		}
		if r.loaded[path] {
			return nil
		}
		if err := r.loadDSL(path); err != nil {
			fmt.Printf("[runtime] load error: %s: %v\n", path, err)
			return nil
		}
		r.loaded[path] = true
		return nil
	})
}

func (r *Runtime) loadDSL(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var root dsl.Root
	if err := json.Unmarshal(data, &root); err != nil {
		return fmt.Errorf("invalid DSL JSON: %w", err)
	}

	for _, p := range root.Pipelines {
		enabled := true
		if p.Enabled != nil {
			enabled = *p.Enabled
		}
		if !enabled {
			continue
		}
		if err := r.schedulePipeline(p); err != nil {
			fmt.Printf("[runtime] schedule pipeline %s error: %v\n", p.ID, err)
		} else {
			fmt.Printf("[runtime] pipeline %s scheduled (%d triggers)\n", p.ID, len(p.Triggers))
		}
	}
	return nil
}

func (r *Runtime) schedulePipeline(p dsl.Pipeline) error {
	c := cron.New(cron.WithSeconds())
	c.Start()

	for _, t := range p.Triggers {
		switch t.Type {
		case "interval":
			dur, err := time.ParseDuration(t.Every)
			if err != nil {
				fmt.Printf("[runtime] pipeline %s: bad interval %q: %v\n", p.ID, t.Every, err)
				continue
			}
			go func(pid string, d time.Duration) {
				tick := time.NewTicker(d)
				defer tick.Stop()
				for range tick.C {
					_ = r.emitInvoke(pid, "interval", map[string]any{
						"every": d.String(),
						"ts":    time.Now().UTC().Format(time.RFC3339Nano),
					})
				}
			}(p.ID, dur)

		case "cron":
			spec := t.Cron
			_, err := c.AddFunc(spec, func() {
				_ = r.emitInvoke(p.ID, "cron", map[string]any{
					"cron": spec,
					"ts":   time.Now().UTC().Format(time.RFC3339Nano),
				})
			})
			if err != nil {
				fmt.Printf("[runtime] pipeline %s: bad cron %q: %v\n", p.ID, spec, err)
			}
		default:
			continue
		}
	}
	return nil
}

func (r *Runtime) emitInvoke(pipelineID, triggerType string, meta map[string]any) error {
	msg := map[string]any{
		"id":          uuid.NewString(),
		"type":        "invoke",
		"pipelineId":  pipelineID,
		"triggerType": triggerType,
		"meta":        meta,
	}
	buf, _ := json.MarshalIndent(msg, "", "  ")
	out := filepath.Join(r.Outbox, fmt.Sprintf("%s.json", msg["id"]))
	return os.WriteFile(out, buf, 0o644)
}
