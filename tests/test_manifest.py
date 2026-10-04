import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ManifestTests(unittest.TestCase):
    def test_issuer_column_survives_cluster_discovery(self):
        columns = {column["id"]: column for column in self.manifest["contributions"]["tableColumns"]}
        self.assertEqual(columns["issuer"]["forKinds"], ["cert-manager.io/Certificate"])
        self.assertEqual(columns["issuer"]["title"], "Issuer")
        self.assertEqual(columns["issuer"]["source"]["jsonPath"], ".spec.issuerRef.name")
        self.assertEqual(columns["issuer"]["format"], "text")
        certificates = next(b for b in self.manifest["capabilities"] if b["name"] == "certificates")
        self.assertNotIn("Issuer", [column["name"] for column in certificates["arguments"]["printerColumns"]])
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "manifest.json").read_text())

    def test_readers_fix_cert_manager_v1_and_namespace_scope(self):
        readers = {b["name"]: b for b in self.manifest["capabilities"]}
        expected = {"certificates": ("Certificate", True), "issuers": ("Issuer", True),
                    "clusterissuers": ("ClusterIssuer", False), "certificaterequests": ("CertificateRequest", True)}
        self.assertEqual(set(readers), set(expected))
        for name, (kind, namespaced) in expected.items():
            with self.subTest(name=name):
                binding = readers[name]
                self.assertEqual(binding["target"], "k8s.listCustomResource")
                args = binding["arguments"]
                self.assertEqual((args["group"], args["version"], args["plural"], args["kind"], args["namespaced"]),
                                 ("cert-manager.io", "v1", name, kind, namespaced))
                self.assertEqual(binding["inputs"], ["context", "namespace"] if namespaced else ["context"])

    def test_all_resource_pages_have_their_own_reader(self):
        pages = self.manifest["contributions"]["pages"]
        self.assertEqual({(p["id"], p["capability"]) for p in pages},
                         {(n, n) for n in ["certificates", "issuers", "clusterissuers", "certificaterequests"]})

    def test_required_contribution_slots_are_present(self):
        for field in ["detailTabs", "detailLinks"]:
            self.assertEqual(self.manifest["contributions"].get(field), [])

    def test_renewal_is_a_confirmed_status_request_on_certificates_only(self):
        self.assertEqual(set(self.manifest["permissions"]), {"k8s.listCustomResource", "k8s.setStatusCondition"})
        actions = self.manifest["actions"]
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual((action["target"], action["resource"]), ("k8s.setStatusCondition", "certificates"))
        self.assertEqual(action["arguments"], {"conditionType":"Issuing","conditionStatus":"True",
            "reason":"ManuallyTriggered","message":"Certificate re-issuance manually triggered"})
        for field in ["preconditions", "availableWhen"]:
            self.assertEqual(action[field][0]["jsonPath"], '.status.conditions[?(@.type=="Issuing")].status')
            self.assertEqual(action[field][0]["notEquals"], "True")
        self.assertEqual(action["name"], "renew")

    def test_issuing_takes_precedence_over_ready_and_requests_check_denial_first(self):
        resolvers = self.manifest["contributions"]["statusResolvers"]
        certificates = next(r for r in resolvers if "cert-manager.io/Certificate" in r["forKinds"])
        self.assertEqual(certificates["rules"][0]["when"][0]["jsonPath"], '.status.conditions[?(@.type=="Issuing")].status')
        self.assertEqual(certificates["rules"][0]["status"], "progressing")
        self.assertEqual(certificates["rules"][1]["when"][0]["equals"], "True")
        self.assertEqual(certificates["rules"][-1]["status"], "unknown")
        requests = next(r for r in resolvers if "cert-manager.io/CertificateRequest" in r["forKinds"])
        self.assertEqual(requests["rules"][0]["when"][0]["jsonPath"], '.status.conditions[?(@.type=="Denied")].status')
        self.assertEqual(requests["rules"][0]["status"], "error")

    def test_expiry_uses_the_declared_window_and_opens_the_same_reader(self):
        setting = self.manifest["settings"][0]
        self.assertEqual((setting["id"], setting["type"], setting["default"]), ("expiryWindow", "select", "14d"))
        self.assertEqual([o["value"] for o in setting["options"]], ["7d", "14d", "30d", "60d", "90d"])
        card = self.manifest["contributions"]["dashboardCards"][0]
        self.assertEqual(card["source"], "certificates")
        self.assertEqual(card["target"]["page"], "certificates")
        self.assertEqual(card["predicate"], {"jsonPath":".status.notAfter","within":"${settings.expiryWindow}"})

    def test_not_after_survives_crd_columns_and_detail_never_reads_secret_values(self):
        contribution = self.manifest["contributions"]
        column = next(c for c in contribution["tableColumns"] if c["title"] == "Not after")
        self.assertEqual(column["source"]["jsonPath"], ".status.notAfter")
        self.assertEqual(column["format"], "date")
        panel = next(p for p in contribution["detailPanels"] if "cert-manager.io/Certificate" in p["forKinds"])
        fields = {f["jsonPath"] for s in panel["sections"] if s["type"] == "fields" for f in s["fields"]}
        self.assertTrue({".status.notAfter", ".status.notBefore", ".status.renewalTime", ".spec.issuerRef.name", ".spec.secretName"} <= fields)
        self.assertTrue(any(s["type"] == "conditions" and s["jsonPath"] == ".status.conditions" for s in panel["sections"]))

if __name__ == "__main__":
    unittest.main()
