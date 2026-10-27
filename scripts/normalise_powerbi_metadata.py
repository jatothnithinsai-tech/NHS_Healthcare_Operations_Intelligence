"""Restore optional schema pointers removed by Desktop Save; validate content."""
import json
from scripts.build_powerbi import BASE,MODEL,REPORT,URLS,save,validate

for path,kind in [(BASE/'NHS_Healthcare_Operations_Intelligence.pbip','pbip'),(MODEL/'definition.pbism','pbism'),(REPORT/'definition.pbir','pbir')]:
    value=json.loads(path.read_text(encoding='utf-8-sig'))
    value['$schema']=URLS[kind]
    save(path,value)
validate()
