/**
 * H1-AI — Dashboard (redirect to enhanced)
 */
Pages.dashboard = {
  async render(el) {
    // redirect للنسخة المحسّنة
    return Pages.dashboard_enhanced.render(el);
  }
};
