import json
import unittest
from datetime import datetime,timedelta
from unittest.mock import patch
from policy import notices,service,sources,contract,explain
from policy.notices import KST

class PolicyTests(unittest.TestCase):
    def test_zero_and_missing(self):
        p=service.validate(dict(district="동작구",monthly=0,personalIncome=None))
        self.assertEqual(p["monthly"],0)
        self.assertNotIn("personalIncome",p)
        for bad in (True,-1,"0",float("inf")):
            with self.assertRaises(ValueError):service.validate(dict(district="동작구",monthly=bad))

    def test_eligibility(self):
        n=dict(detailUrl="source",rules=[("resident","eq","yes"),("householdIncome","le",3000)])
        f=notices.evaluate(n,dict(resident="planned",personalIncome=1000))
        self.assertEqual([x["status"] for x in f],["불충족","확인 필요"])

    def test_admission(self):
        n=dict(notices.NOTICE,closure=None,anchors=["회차 일치"],openPattern="접수 중",
               deadline="2026-11-30T18:00:00+09:00")
        text="회차 일치 접수 중"
        now=datetime(2026,11,21,tzinfo=KST)
        for at,t,want in [(now,text,"접수 중"),(now,text+" (모집마감)","조기 마감·예산 소진"),
            (datetime(2026,11,30,18,tzinfo=KST),text,"기간 종료"),
            (datetime(2026,1,1,tzinfo=KST),text,"접수 예정"),(now,"접수 중","확인 불가")]:
            self.assertEqual(notices.admission(n,t,at),want)

    def test_sources_and_region(self):
        forms={"동작구":"a"*32,"관악구":"b"*32}
        directory="전월세 계약상담 집보기 동행 서울시 거주 또는 거주예정1인가구(독립가구예정인자 포함)"
        for d,i in forms.items():
            directory+=f'<a href="/front/bsns/bsnsApplcntStep1Page.do?bsns_id={i}">{d} 신청하기</a>'
        def fetch(url):
            if url==contract.PORTAL:return directory
            if url==contract.ANNUAL:return "2026 전월세 안심계약 도움서비스 운영 20260101 ~ 20261231"
            if url.endswith(tuple(forms.values())):
                d=next(d for d,i in forms.items() if url.endswith(i))
                return f"[{d}] 1인가구 전월세 안심계약 도움서비스 이용대상 무료 독립가구예정인자 포함 이용안내 동의 하기 <button>다음</button>"
            raise sources.SourceError("연결 실패")
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None): return cls(2026,11,21,tzinfo=KST)
        with patch("policy.contract.fetch",side_effect=fetch),patch("policy.contract.datetime",Clock),patch.dict("os.environ",{},clear=True):
            for d,i in forms.items():
                p={"district":d,"locationIntent":"yes"}
                result=service.lookup(p)
                self.assertIn("single",result["requiredFields"])
                p["single"]="yes"
                result=service.lookup(p)
                self.assertEqual(result["state"],"results")
                self.assertTrue(result["partial"])
                item=result["recommendations"][0]
                self.assertTrue(item["applyUrl"].endswith(i))
                self.assertEqual(item["regions"],[d])
                self.assertEqual(service.lookup(dict(p,single="no"))["state"],"empty")
                with patch("policy.contract.fetch",side_effect=sources.SourceError("연결 실패")):
                    self.assertEqual(service.lookup(p,item["policyId"])["recommendations"],[])

    def test_pagination(self):
        def get(url):
            start=int(url.split("/")[-3])
            rows=[{"id":i} for i in range(start,min(start+500,503))]
            return json.dumps({"svc":{"RESULT":{"CODE":"INFO-000"},"list_total_count":502,"row":rows}})
        with patch.object(sources,"fetch",side_effect=get):
            self.assertEqual(len(sources.seoul_table("svc","sample")),502)
        with patch.object(sources,"fetch",return_value='{"RESULT":{"CODE":"ERROR-300"}}'):
            with self.assertRaises(sources.SourceError):sources.seoul_table("svc","key")

    def test_gemini_validation(self):
        item=dict(policyId="test",findings=[dict(label="만 나이")])
        fallback="만 나이 조건을 충족해요."
        ans=dict(policyId="other",refs=["0"],explanation="지원금 99만원")
        response=json.dumps({"candidates":[{"content":{"parts":[{"text":json.dumps(ans)}]}}]})
        with patch.dict("os.environ",{"GEMINI_API_KEY":"test","GEMINI_MODEL":"test"}),patch.object(explain,"fetch",return_value=response):
            self.assertEqual(explain.explain(item)[0],fallback)

    def test_failures(self):
        with patch.dict("os.environ",{},clear=True),patch("policy.contract.fetch",side_effect=sources.SourceError("조회 실패")):
            self.assertEqual(service.lookup({"district":"동작구"})["state"],"failed")

