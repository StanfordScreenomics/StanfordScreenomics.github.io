import pandas as pd
from scholarly import scholarly
from habanero import Crossref
import time

cr = Crossref()
author_id = "V6mIZuYAAAAJ"

# Get author info and publications
author = scholarly.search_author_id(author_id)
author_filled = scholarly.fill(author, sections=['publications'])

pub_list = []
keywords = ['screenome', 'screenomes', 'screenomics', 'screenshots', 'digital trace', 'smartphone']

for pub in author_filled['publications']:
    pub_year = pub['bib'].get('pub_year')
    title = pub['bib'].get('title', '')
    abstract = pub['bib'].get('abstract', '').lower()
    scholar_url = pub.get('pub_url', '')
    citations = pub.get('num_citations', 0)

    if pub_year and int(pub_year) >= 2019:
        title_lower = title.lower()
        if any(k in title_lower for k in keywords) or any(k in abstract for k in keywords):
            # Try to get full metadata from CrossRef
            try:
                res = cr.works(query_title=title, limit=1)
                item = res['message']['items'][0]

                # Format authors
                authors = item.get('author', [])
                if authors:
                    author_str = ', '.join([f"{a['family']}, {a['given'][0]}." for a in authors])
                else:
                    author_str = pub['bib'].get('author', 'Author')

                # Get journal info
                journal = item.get('container-title', [''])[0]
                volume = item.get('volume', '')
                issue = item.get('issue', '')
                pages = item.get('page', '')
                doi = item.get('DOI', '')

                apa_citation = f"{author_str} ({pub_year}). {title}. {journal}"
                if volume:
                    apa_citation += f", {volume}"
                    if issue:
                        apa_citation += f"({issue})"
                if pages:
                    apa_citation += f", {pages}"
                if doi:
                    apa_citation += f". https://doi.org/{doi}"
                else:
                    apa_citation += f". {scholar_url}"

                pub_list.append({
                    'title': title,
                    'year': pub_year,
                    'journal': journal,
                    'citations': citations,
                    'scholar_url': scholar_url,
                    'apa_citation': apa_citation
                })
                time.sleep(1)  # polite pause to avoid hitting API rate limits
            except Exception as e:
                print(f"Failed to fetch CrossRef data for '{title}': {e}")
                # fallback to basic APA
                authors = pub['bib'].get('author', 'Author')
                apa_citation = f"{authors} ({pub_year}). {title}. {scholar_url}"
                pub_list.append({
                    'title': title,
                    'year': pub_year,
                    'journal': journal,
                    'citations': citations,
                    'scholar_url': scholar_url,
                    'apa_citation': apa_citation
                })

# Save to CSV
df = pd.DataFrame(pub_list)

# Sort by year, most recent on top
df = df.sort_values(by='year', ascending=False)

df.to_csv("screenomics_publications_since_2019.csv", index=False)
print(f"Saved {len(pub_list)} publications to CSV.")
