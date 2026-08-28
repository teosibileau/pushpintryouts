# One record: ppchat.corvus.observer -> the throwline box. The zone
# belongs to the MOVE platform root (~/DEV/MOVE/platform/infra), which
# owns every zone-level setting (SSL mode, cert packs, Origin CA); this
# root must never touch those, and MOVE's must never define this record.
# *.corvus.observer is already covered at the edge (Universal cert) and
# at the origin (the Origin CA wildcard), so a record is all it takes.
#
# State is local and git-ignored (a single DNS record; if it's ever
# lost: tofu import cloudflare_dns_record.ppchat <zone_id>/<record_id>).
#
# Auth: CLOUDFLARE_API_TOKEN and TF_VAR_cloudflare_zone_id from
# .env.infra (same values the MOVE root uses).

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5"
    }
  }
}

provider "cloudflare" {}

variable "cloudflare_zone_id" {
  description = "Zone id of corvus.observer (MOVE's Cloudflare zone)."
  type        = string
}

variable "ppchat_ip" {
  description = "IPv4 of the box serving ppchat (the throwline Hetzner box)."
  type        = string
  default     = "178.156.153.244"
}

resource "cloudflare_dns_record" "ppchat" {
  zone_id = var.cloudflare_zone_id
  name    = "ppchat.corvus.observer"
  type    = "A"
  content = var.ppchat_ip
  proxied = true
  ttl     = 1 # auto (mandatory on proxied records)
}
