import { useEffect, useMemo, useState, type FormEvent } from 'react'

const API = 'http://localhost:8000'

type Inventory = { size: string; quantity: number }
type User = { id: number; first_name: string; last_name: string; email: string }
type Product = {
  product_id: string; name: string; garment_type: string; description: string
  colors: string[]; image_file_path: string; price: number; total_stock: number
  inventory?: Inventory[]
}

function imageUrl(path: string) { return `${API}/images/${path}` }

function go(path: string) {
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

function Header({ path, user, onLogOut }: { path: string; user?: User; onLogOut: () => void }) {
  const links = [['/', 'Home'], ['/products', 'Products'], ['/about', 'About us']]
  return <header className="site-header">
    <a className="brand" href="#" onClick={(e) => { e.preventDefault(); go('/') }}>
      <span className="brand-mark">CC</span><span>Campus <em>Customs</em></span>
    </a>
    <nav aria-label="Main navigation">
      {links.map(([href, label]) => <a key={href} className={path === href || (href === '/products' && path.startsWith('/products/')) ? 'active' : ''} href={`#${href}`} onClick={(e) => { e.preventDefault(); go(href) }}>{label}</a>)}
    </nav>
    <div className="account-links">{user ? <><span className="signed-in">Hi, {user.first_name}</span><button className="logout-link" onClick={onLogOut}>Log out</button></> : <><a href="#/login" onClick={(e) => { e.preventDefault(); go('/login') }}>Log in</a><a className="account-button" href="#/create-account" onClick={(e) => { e.preventDefault(); go('/create-account') }}>Create account</a></>}</div>
  </header>
}

function Home({ onBrowse }: { onBrowse: () => void }) {
  return <main>
    <section className="hero">
      <div className="hero-copy"><p className="eyebrow">YALE SPIRIT, YOUR WAY</p><h1>Wear a little<br /><span>Blue.</span></h1><p className="hero-lede">Thoughtful layers, familiar marks, and pieces that feel right long after the walk across campus.</p><button className="button button-light" onClick={onBrowse}>Shop the collection <span>↗</span></button></div>
      <div className="hero-art"><div className="sun"></div><div className="arch arch-one"></div><div className="arch arch-two"></div><div className="hero-note">Est.<br /><strong>1701</strong></div></div>
    </section>
    <section className="welcome section"><div><p className="eyebrow">FROM NEW HAVEN, WITH CARE</p><h2>Made for the people<br />who make <i>Yale.</i></h2></div><p className="body-copy">Campus Customs is a considered collection of Yale favorites—kept close, worn often, and chosen with a little more intention. Find something for a friend, a new chapter, or simply yourself.</p></section>
    <section className="feature-strip"><div><p className="eyebrow">THE CAMPUS EDIT</p><h2>Good-looking<br /><i>essentials.</i></h2></div><div className="feature-card"><span>01 / 03</span><p>Soft layers for crisp mornings, late afternoons, and everywhere in between.</p><button className="text-button" onClick={onBrowse}>Explore products <span>→</span></button></div></section>
  </main>
}

function ProductGrid({ products, showDescription = false }: { products: Product[]; showDescription?: boolean }) {
  return <div className="product-grid">{products.map(product => <a className="product-card" key={product.product_id} href={`#/products/${product.product_id}`} onClick={(e) => { e.preventDefault(); go(`/products/${product.product_id}`) }}><div className="product-image"><img src={imageUrl(product.image_file_path)} alt={product.name} loading="lazy" /><span className="product-type-chip">{product.garment_type}</span><span className="card-arrow">↗</span></div><div className="product-card-copy"><h3>{product.name}</h3><p>{showDescription ? product.description : product.garment_type}</p><strong>${product.price.toFixed(2)}</strong></div></a>)}</div>
}

function Products({ products, loading, chatResults, onClearChatResults }: { products: Product[]; loading: boolean; chatResults: Product[]; onClearChatResults: () => void }) {
  const [search, setSearch] = useState('')
  const [garmentType, setGarmentType] = useState('')
  const [inStockOnly, setInStockOnly] = useState(false)
  const garmentTypes = useMemo(() => [...new Set(products.map(product => product.garment_type))].sort(), [products])
  const visible = useMemo(() => products.filter(product => `${product.name} ${product.garment_type} ${product.description}`.toLowerCase().includes(search.toLowerCase()) && (!garmentType || product.garment_type === garmentType) && (!inStockOnly || product.total_stock > 0)), [products, search, garmentType, inStockOnly])
  return <main className="section products-page">{chatResults.length > 0 && <section className="chat-results" aria-live="polite"><div className="chat-results-heading"><div><p className="eyebrow">CAMPUS CONCIERGE PICKS</p><h2>Just for <i>you.</i></h2><p>{chatResults.length} matching {chatResults.length === 1 ? 'piece' : 'pieces'} from your chat search.</p></div><button className="text-button" onClick={onClearChatResults}>Clear results ×</button></div><ProductGrid products={chatResults} showDescription /></section>}<div className="page-intro"><div><p className="eyebrow">THE COLLECTION</p><h1>Find your <i>favorite.</i></h1></div><p>Yale pieces for everyday rituals, big moments, and all the little ones in between.</p></div><div className="product-tools"><span>{visible.length} pieces</span><div className="catalogue-filters"><label><span className="sr-only">Search products</span><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search the collection" /></label><label className="select-filter"><span className="sr-only">Garment type</span><select value={garmentType} onChange={(e) => setGarmentType(e.target.value)}><option value="">All styles</option>{garmentTypes.map(type => <option key={type} value={type}>{type}</option>)}</select></label><label className="stock-filter"><input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} /> In stock</label></div></div>{loading ? <p className="status">Gathering the collection…</p> : <ProductGrid products={visible} />}</main>
}

function ProductDetail({ product, loading, onBack }: { product?: Product; loading: boolean; onBack: () => void }) {
  if (loading) return <main className="section status">Opening the product details…</main>
  if (!product) return <main className="section status"><h2>We couldn’t find that piece.</h2><button className="button button-blue" onClick={onBack}>Back to products</button></main>
  return <main className="detail-page"><button className="back-link" onClick={onBack}>← Back to collection</button><div className="detail-layout"><div className="detail-image"><img src={imageUrl(product.image_file_path)} alt={product.name} /></div><div className="detail-copy"><p className="eyebrow">CAMPUS CUSTOMS / {product.garment_type}</p><h1>{product.name}</h1><p className="detail-price">${product.price.toFixed(2)}</p><p className="detail-description">{product.description}</p><div className="rule"></div><p className="label">AVAILABLE SIZES</p><div className="sizes">{(product.inventory ?? []).map(item => <span className={item.quantity > 0 ? '' : 'sold-out'} key={item.size}>{item.size}<small>{item.quantity > 0 ? `${item.quantity} left` : 'sold out'}</small></span>)}</div><button className="button button-blue add-button">Add to bag <span>→</span></button><p className="fine-print">Stock is shown live from our shop catalogue. Questions? Ask our Campus Concierge below.</p></div></div></main>
}

function About() { return <main className="section about-page"><p className="eyebrow">A SMALL SHOP WITH A BIG HEART</p><h1>For the love<br />of <i>Yale.</i></h1><div className="about-columns"><p className="lead">We believe the best Yale things are the ones that become part of your everyday. A crewneck on a cool morning. A favorite tee on a long weekend. A gift that says, “I know you.”</p><div><p>Campus Customs brings together comfortable, well-made pieces inspired by the people, places, and traditions that make this campus feel like home. We keep the collection easy to browse and the experience warm because shopping for spirit wear should feel personal.</p><p>Whether you are heading to New Haven for the first time or finding your way back, there is always room for a little more Blue.</p></div></div></main> }

function Account({ create = false, onSuccess }: { create?: boolean; onSuccess: (user: User) => void }) {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault(); setError('')
    if (create && password !== confirmPassword) { setError('Passwords do not match.'); return }
    setSubmitting(true)
    try {
      const response = await fetch(`${API}/api/auth/${create ? 'register' : 'login'}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(create ? { first_name: firstName, last_name: lastName, email, password } : { email, password }) })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'We could not complete that request.')
      onSuccess(result.user)
    } catch (err) { setError(err instanceof Error ? err.message : 'We could not complete that request.') } finally { setSubmitting(false) }
  }
  return <main className="section account-page"><p className="eyebrow">CAMPUS CUSTOMS</p><h1>{create ? 'Make yourself at home.' : 'Welcome back.'}</h1><p className="body-copy">{create ? 'Create an account to keep your favorite pieces close.' : 'Log in to view your saved pieces and details.'}</p><form className="account-form" onSubmit={submit}>{create && <><label>First name<input required value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Ada" /></label><label>Last name<input required value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Lovelace" /></label></>}<label>Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" /></label><label>Password<input required minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" /></label>{create && <label>Confirm password<input required minLength={8} type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" /></label>}{error && <p className="form-error" role="alert">{error}</p>}<button className="button button-blue" type="submit" disabled={submitting}>{submitting ? 'Working…' : create ? 'Create account' : 'Log in'} <span>→</span></button></form></main>
}

type ChatMessage = { role: 'user' | 'assistant'; content: string; products?: Product[] }
type PageContext = { product_id: string; product_name: string }
const WELCOME_MESSAGE: ChatMessage = { role: 'assistant', content: 'Hello! I can help you find a piece, check a price, or see what is in stock.' }

function ChatStub({ userId, pageContext, onProductsMatched }: { userId?: number; pageContext?: PageContext; onProductsMatched: (products: Product[]) => void }) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE])
  useEffect(() => {
    let current = true
    if (!userId) { setMessages([WELCOME_MESSAGE]); return () => { current = false } }
    fetch(`${API}/api/chat/history/${userId}`).then(response => response.ok ? response.json() : Promise.reject()).then(result => {
      if (current) setMessages(result.messages?.length ? result.messages : [WELCOME_MESSAGE])
    }).catch(() => { if (current) setMessages([WELCOME_MESSAGE]) })
    return () => { current = false }
  }, [userId])
  async function sendMessage(event?: { preventDefault: () => void }) {
    event?.preventDefault(); const message = draft.trim(); if (!message || sending) return
    const nextMessages = [...messages, { role: 'user' as const, content: message }]
    setMessages(nextMessages); setDraft(''); setSending(true)
    try {
      const response = await fetch(`${API}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, user_id: userId, page_context: pageContext, history: messages.slice(-10).map(({ role, content }) => ({ role, content })) }) })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'The concierge is unavailable right now.')
      setMessages([...nextMessages, { role: 'assistant', content: result.reply, products: result.products }])
      if (result.products?.length && !pageContext) { onProductsMatched(result.products); go('/products') }
    } catch (error) { setMessages([...nextMessages, { role: 'assistant', content: error instanceof Error ? error.message : 'The concierge is unavailable right now.' }]) } finally { setSending(false) }
  }
  const quickPrompts = ['Show me hoodies', 'Yale gifts under $50', 'What is in stock?']
  return <div className="chat-wrap">{open && <div className="chat-panel"><div className="chat-heading"><p className="eyebrow">CAMPUS CONCIERGE</p><button className="close-chat" onClick={() => setOpen(false)} aria-label="Close chat">×</button><h3>How can we help?</h3></div><div className="quick-prompts" aria-label="Suggested questions">{quickPrompts.map(prompt => <button key={prompt} onClick={() => setDraft(prompt)}>{prompt}</button>)}</div><div className="chat-messages">{messages.map((item, index) => <div className={`chat-message ${item.role}`} key={`${item.role}-${index}`}><p>{item.content}</p>{item.products && item.products.length > 0 && <div className="chat-products">{item.products.slice(0, 3).map(product => <button key={product.product_id} onClick={() => { setOpen(false); go(`/products/${product.product_id}`) }}><img src={imageUrl(product.image_file_path)} alt="" /><span>{product.name}<small>${product.price.toFixed(2)}</small></span></button>)}</div>}</div>)}{sending && <div className="chat-message assistant"><p className="typing">Looking through the collection…</p></div>}</div><form className="chat-input" onSubmit={sendMessage}><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Ask about the collection" aria-label="Ask the Campus Concierge" disabled={sending} /><button type="submit" aria-label="Send message" disabled={sending || !draft.trim()}>↗</button></form></div>}<button className="chat-button" onClick={() => setOpen(!open)} aria-label="Open Campus Concierge"><span>✦</span>{open ? 'Close' : 'Chat with us'}</button></div>
}

export default function App() {
  const [path, setPath] = useState(window.location.pathname)
  const [user, setUser] = useState<User | undefined>(() => { const saved = localStorage.getItem('campus-customs-user'); return saved ? JSON.parse(saved) : undefined })
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<Product>()
  const [detailLoading, setDetailLoading] = useState(false)
  const [chatResults, setChatResults] = useState<Product[]>([])
  useEffect(() => { const listener = () => setPath(window.location.pathname); window.addEventListener('popstate', listener); return () => window.removeEventListener('popstate', listener) }, [])
  useEffect(() => { fetch(`${API}/api/products`).then(r => r.json()).then(setProducts).catch(() => setProducts([])).finally(() => setLoading(false)) }, [])
  useEffect(() => { if (!path.startsWith('/products/')) { setDetail(undefined); setDetailLoading(false); return }; setDetail(undefined); setDetailLoading(true); fetch(`${API}/api/products/${path.split('/')[2]}`).then(r => r.ok ? r.json() : undefined).then(setDetail).catch(() => setDetail(undefined)).finally(() => setDetailLoading(false)) }, [path])
  function signedIn(nextUser: User) { setUser(nextUser); localStorage.setItem('campus-customs-user', JSON.stringify(nextUser)); go('/') }
  function logOut() { setUser(undefined); localStorage.removeItem('campus-customs-user'); go('/') }
  const pageContext = path.startsWith('/products/') && detail ? { product_id: detail.product_id, product_name: detail.name } : undefined
  let page = path === '/' ? <Home onBrowse={() => go('/products')} /> : path === '/products' ? <Products products={products} loading={loading} chatResults={chatResults} onClearChatResults={() => setChatResults([])} /> : path.startsWith('/products/') ? <ProductDetail product={detail} loading={detailLoading} onBack={() => go('/products')} /> : path === '/about' ? <About /> : path === '/login' ? <Account onSuccess={signedIn} /> : path === '/create-account' ? <Account create onSuccess={signedIn} /> : <Home onBrowse={() => go('/products')} />
  return <><Header path={path} user={user} onLogOut={logOut} />{page}<ChatStub userId={user?.id} pageContext={pageContext} onProductsMatched={setChatResults} /><footer><span>Campus Customs</span><span>Made with care in New Haven.</span><span>© 2026</span></footer></>
}
