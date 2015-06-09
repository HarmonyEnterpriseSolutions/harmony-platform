package gnue.forms.ui;


abstract class URLViewer extends WidgetNavigable {
	public URLViewer(Desktop desktop, Integer id, String label) {
		super(desktop, id, label);
	}
	public abstract void uiSetUrl(String url);

	public boolean isVerticalGrowable() {
		return true;
	}

}
